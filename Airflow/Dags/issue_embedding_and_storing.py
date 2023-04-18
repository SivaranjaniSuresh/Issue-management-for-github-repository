import os
import datetime
import json
import requests
from dotenv import load_dotenv
import snowflake.connector
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
import re
import numpy as np
from transformers import BertTokenizer, BertModel
import torch
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)

load_dotenv()

SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")
SNOWFLAKE_TABLE = os.environ.get("SNOWFLAKE_TABLE")


access_token = os.environ.get("access_token")

conn = snowflake.connector.connect(
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    account=SNOWFLAKE_ACCOUNT,
    warehouse=SNOWFLAKE_WAREHOUSE,
    database=SNOWFLAKE_DATABASE,
    schema=SNOWFLAKE_SCHEMA,
    table=SNOWFLAKE_TABLE,
)

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', max_length=1024)
model = BertModel.from_pretrained('bert-base-uncased')
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def get_all_issues(owner, repo, access_token):
    cursor = conn.cursor()
    result = cursor.execute("SELECT MAX(UPDATED_AT) FROM GITHUB_ISSUES.PUBLIC.ISSUES")
    last_updated_at = result.fetchone()[0]
    # Increment last_updated_at by 1 second
    if last_updated_at is not None:
        last_updated_at = datetime.datetime.fromisoformat(
            last_updated_at.replace("Z", "+00:00")
        )
        last_updated_at += datetime.timedelta(seconds=1)
        last_updated_at = last_updated_at.isoformat().replace("+00:00", "Z")

    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github+json",
    }
    issues = []
    page = 1
    per_page = 100

    while True:
        params = {
            "state": "all",
            "since": last_updated_at,
            "per_page": 100,
            "page": page,
        }
        response = requests.get(url, headers=headers, params=params)
        new_issues = response.json()

        if not new_issues:
            break

        for issue in new_issues:
            if issue["body"]:
                issue_number = issue["number"]
                comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
                reactions_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/reactions"
                comments_response = requests.get(comments_url, headers=headers)
                reactions_response = requests.get(reactions_url, headers=headers)

                if (
                    comments_response.status_code == 200
                    and reactions_response.status_code == 200
                ):
                    comments_data = comments_response.json()
                    reactions_data = reactions_response.json()
                    issue["comments"] = comments_data
                    issue["reactions"] = reactions_data
                    issues.append(issue)
                else:
                    print(
                        f"Error fetching comments or reactions for issue {issue_number}"
                    )

        page += 1

    return issues


def store_issues_in_snowflake(issues, owner, repo):
    cursor = conn.cursor()

    for issue in issues:
        comments_dict = {}
        for comment in issue["comments"]:
            comment_id = comment["id"]
            comments_dict[f"comment {comment_id}"] = comment["body"]

        comments_json = json.dumps(comments_dict)

        reactions_dict = []
        for reaction in issue["reactions"]:
            reaction_dict = {
                "id": reaction["id"],
                "user_login": reaction["user"]["login"],
                "user_id": reaction["user"]["id"],
                "content": reaction["content"],
                "created_at": reaction["created_at"],
            }
            reactions_dict.append(reaction_dict)

        reactions_json = json.dumps(reactions_dict)

        body = issue["body"]
        issue_url = issue["html_url"]
        assignees = ", ".join([assignee["login"] for assignee in issue["assignees"]])
        labels = ", ".join([label["name"] for label in issue["labels"]])
        milestone = issue["milestone"]["title"] if issue["milestone"] else "None"

        query = """
            MERGE INTO GITHUB_ISSUES.PUBLIC.ISSUES USING (
                SELECT %(id)s AS id, %(issue_url)s AS issue_url, %(repo_owner)s AS repo_owner, %(repo_name)s AS repo_name,
                %(issue_number)s AS issue_number, %(created_by)s AS created_by, %(title)s AS title,
                %(body)s AS body, %(comments)s AS comments, %(reactions)s AS reactions, %(assignees)s AS assignees, %(labels)s AS labels, %(milestone)s AS milestone,
                %(state)s AS state, %(updated_at)s AS updated_at
            ) S
            ON ISSUES.ID = S.ID
            WHEN MATCHED THEN
                UPDATE SET ISSUES.ISSUE_URL = S.ISSUE_URL, ISSUES.REPO_OWNER = S.REPO_OWNER, ISSUES.REPO_NAME = S.REPO_NAME,
                ISSUES.ISSUE_NUMBER = S.ISSUE_NUMBER, ISSUES.CREATED_BY = S.CREATED_BY, ISSUES.TITLE = S.TITLE,
                ISSUES.BODY = S.BODY, ISSUES.COMMENTS = S.COMMENTS, ISSUES.REACTIONS = S.REACTIONS, ISSUES.ASSIGNEES = S.ASSIGNEES, ISSUES.LABELS = S.LABELS, ISSUES.MILESTONE = S.MILESTONE,
                ISSUES.STATE = S.STATE, ISSUES.UPDATED_AT = S.UPDATED_AT
            WHEN NOT MATCHED THEN
                INSERT (ID, ISSUE_URL, REPO_OWNER, REPO_NAME, ISSUE_NUMBER, CREATED_BY, TITLE, BODY, COMMENTS, REACTIONS, ASSIGNEES, LABELS, MILESTONE, STATE, UPDATED_AT)
                VALUES (S.ID, S.ISSUE_URL, S.REPO_OWNER, S.REPO_NAME, S.ISSUE_NUMBER, S.CREATED_BY, S.TITLE, S.BODY, S.COMMENTS, S.REACTIONS, S.ASSIGNEES, S.LABELS, S.MILESTONE, S.STATE, S.UPDATED_AT);
        """
        cursor.execute(
            query,
            {
                "id": issue["id"],
                "issue_url": issue_url,
                "repo_owner": owner,
                "repo_name": repo,
                "issue_number": issue["number"],
                "created_by": issue["user"]["login"],
                "title": issue["title"],
                "body": body,
                "comments": comments_json,
                "reactions": reactions_json,
                "assignees": assignees,
                "labels": labels,
                "milestone": milestone,
                "state": issue["state"],
                "updated_at": issue["updated_at"],
            },
        )
        conn.commit()

    cursor.close()

def preprocess_text(text):
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    # Tokenize the text using the BERT tokenizer
    tokens = tokenizer.tokenize(text)

    # Convert tokens to IDs
    token_ids = tokenizer.convert_tokens_to_ids(tokens)
    
    return token_ids

def preprocess_closed_issue_data():
    cursor = conn.cursor()

    # Execute query to select all rows from the ISSUES table
    cursor.execute("SELECT * FROM GITHUB_ISSUES.PUBLIC.ISSUES")

    # Fetch all rows
    rows = cursor.fetchall()

    preprocessed_texts = {}
    
    # Iterate over rows and preprocess the BODY column
    for row in rows:
        issue_number = row[0]  # Assuming ISSUE_NUMBER column is at index 0
        body_text = row[7]  # Assuming BODY column is at index 6
        preprocessed_text = preprocess_text(body_text)
        # Convert token IDs to strings and join them
        tokenized_text = ' '.join([str(token_id) for token_id in preprocessed_text])
        
        preprocessed_texts[issue_number] = tokenized_text
        
    # Close cursor and connection
    cursor.close()
    conn.close()

    return preprocessed_texts

def get_issue_embeddings(tokenized_issue_data, max_chunk_size=512):
    tokenized_texts = list(tokenized_issue_data.values())
    issue_numbers = list(tokenized_issue_data.keys())

    def bert_embedding(text):
        if isinstance(text, list):
            text = text[0]
        token_ids = list(map(int, text.split()))

        if len(token_ids) < max_chunk_size:
            token_id_chunks = [token_ids]
        else:
            token_id_chunks = [token_ids[i:i + max_chunk_size] for i in range(0, len(token_ids), max_chunk_size)]

        chunk_embeddings = []
        with torch.no_grad():
            for chunk in token_id_chunks:
                if not chunk:
                    continue
                embedding = model(torch.tensor(chunk).unsqueeze(0).to(device))[1].squeeze().cpu().numpy()
                chunk_embeddings.append(embedding)
        avg_embedding = np.zeros(768) if not chunk_embeddings else np.mean(chunk_embeddings, axis=0)
        return avg_embedding

    issue_embeddings = {}
    for issue_number, text in zip(issue_numbers, tokenized_texts):
        embedding = bert_embedding(text)
        issue_embeddings[issue_number] = embedding.tolist()  # Convert numpy array to list

    print(issue_embeddings)
    return issue_embeddings

def store_embeddings_in_milvus(issue_embeddings):
    data_dict = issue_embeddings

    primary_keys = [key for key in data_dict.keys()]
    vectors = list(data_dict.values())
    dim = len(vectors[0])  # Set the dimension based on the length of the first vector

    # Connect to Milvus
    connections.connect("default", host="34.138.127.169", port="19530")

    utility.drop_collection("my_collection")

    # Create collection
    fields = [
        FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=dim)
    ]

    schema = CollectionSchema(fields, "My collection with primary keys and vector embeddings")
    my_collection = Collection("my_collection", schema, consistency_level="Strong")

    # Insert data
    entities = [
        primary_keys,
        vectors
    ]

    insert_result = my_collection.insert(entities)
    my_collection.flush()

    # Create index
    index = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128},
    }
    my_collection.create_index("embeddings", index)

    # Load data into memory
    my_collection.load()

    print("Done")
    # Perform other operations like search, query, etc., as needed
    # Fetch all records from the collection using primary key values
    all_records = my_collection.query(f"pk in {primary_keys}", output_fields=["pk", "embeddings"])

    results_dict = {}
    # Populate the dictionary with fetched records
    for record in all_records:
        results_dict[int(record['pk'])] = record['embeddings']

    print(results_dict)



default_args = {
    "owner": "airflow",
    "start_date": datetime.datetime(2023, 4, 17),
    "retries": 2,
    "retry_delay": datetime.timedelta(minutes=5),
}

dag = DAG(
    'github_issue_data_pipeline',
    default_args=default_args,
    description='A pipeline to fetch GitHub issue data, store it in Snowflake, and compute embeddings',
    schedule_interval=datetime.timedelta(days=1),
    catchup=False,
)

def fetch_and_store_github_issues(**kwargs):
    owner = "openai"
    repo = "openai-python"
    issues = get_all_issues(owner, repo, access_token)
    store_issues_in_snowflake(issues, owner, repo)

def compute_embeddings(**kwargs):
    preprocessed_issue_data = preprocess_closed_issue_data()
    issue_embeddings = get_issue_embeddings(preprocessed_issue_data)
    issue_ids = []
    for issue_id, embedding in issue_embeddings.items():
        issue_ids.append(issue_id)
        kwargs["ti"].xcom_push(key=str(issue_id), value=embedding)
    kwargs["ti"].xcom_push(key="issue_ids", value=issue_ids)


def store_embeddings_in_milvus_task(**kwargs):
    issue_ids = kwargs["ti"].xcom_pull(key="issue_ids")
    issue_embeddings = {}
    for issue_id in issue_ids:
        embedding = kwargs["ti"].xcom_pull(key=str(issue_id))
        issue_embeddings[int(issue_id)] = embedding  # Convert the issue ID to an integer
    store_embeddings_in_milvus(issue_embeddings)

fetch_and_store_github_issues_task = PythonOperator(
    task_id="fetch_and_store_github_issues",
    python_callable=fetch_and_store_github_issues,
    provide_context=True,
    dag=dag,
)

compute_embeddings_task = PythonOperator(
    task_id='compute_embeddings',
    python_callable=compute_embeddings,
    dag=dag,
)

store_embeddings_in_milvus_task = PythonOperator(
    task_id="store_embeddings_in_milvus",
    python_callable=store_embeddings_in_milvus_task,
    provide_context=True,
    dag=dag,
)

fetch_and_store_github_issues_task >> compute_embeddings_task >> store_embeddings_in_milvus_task
