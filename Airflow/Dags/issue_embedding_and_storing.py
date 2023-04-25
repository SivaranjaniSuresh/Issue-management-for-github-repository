import datetime
import json
import os
import re

import requests
import snowflake.connector
from airflow.operators.python_operator import PythonOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from dotenv import load_dotenv

from airflow import DAG

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

default_args = {
    "owner": "airflow",
    "start_date": datetime.datetime(2023, 4, 17),
    "retries": 2,
    "retry_delay": datetime.timedelta(minutes=2),
}

dag = DAG(
    "embedding",
    default_args=default_args,
    description="A pipeline to fetch GitHub issue data, store it in Snowflake, and compute embeddings",
    schedule_interval=datetime.timedelta(days=1),
    catchup=False,
)


def get_owner_repo_pairs_from_snowflake():
    """
    Retrieve distinct owner-repo pairs from the GITHUB_ISSUES.PUBLIC.REPO table in Snowflake.

    Returns:
    owner_repo_pairs : list of tuples
        A list of tuples where each tuple represents an owner-repo pair.
        The first element in the tuple represents the owner of the repository, and the second element
        represents the name of the repository.
    """
    query = "SELECT DISTINCT(REPO_OWNER), REPO_NAME FROM GITHUB_ISSUES.PUBLIC.REPO"
    cur = conn.cursor()
    cur.execute(query)

    # Convert the result into a list of tuples
    owner_repo_pairs = [tuple(row) for row in cur.fetchall()]
    print(owner_repo_pairs)
    # Close the connection
    cur.close()
    return owner_repo_pairs


def get_all_issues(owner, repo, access_token):
    """
    Fetches all issues from the specified GitHub repository that have been updated since the last time they were retrieved.

    Args:
        owner (str): The owner of the GitHub repository.
        repo (str): The name of the GitHub repository.
        access_token (str): A GitHub access token for authentication.

    Returns:
        List[Dict]: A list of dictionaries representing the issues, where each dictionary contains the issue's information, such as title, body, comments, and reactions.
    """
    cursor = conn.cursor()
    result = cursor.execute(
        f"SELECT MAX(UPDATED_AT) FROM GITHUB_ISSUES.PUBLIC.ISSUES WHERE REPO_OWNER='{owner}' AND REPO_NAME='{repo}'"
    )
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
    """
    Store GitHub issues in a Snowflake database.

    Parameters:
    - issues (list of dicts): A list of dictionaries representing GitHub issues.
    - owner (str): The owner of the GitHub repository.
    - repo (str): The name of the GitHub repository.

    Returns:
    - None

    Raises:
    - None
    """
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

        # Define an empty list to store the rows
        rows = []

        # Create a dictionary representing the current row
        row = {
            "id": issue["id"],
            "issue_url": issue["html_url"],
            "repo_owner": owner,
            "repo_name": repo,
            "issue_number": issue["number"],
            "created_by": issue["user"]["login"],
            "title": issue["title"],
            "body": issue["body"],
            "comments": comments_dict,
            "reactions": reactions_dict,
            "assignees": assignees,
            "labels": labels,
            "milestone": milestone,
            "state": issue["state"],
            "updated_at": issue["updated_at"],
        }

        # Append the row to the list
        rows.append(row)

        # Create the DataFrame
        df = pd.DataFrame(rows)

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


import numpy as np
import pandas as pd
import torch
from transformers import BertModel, BertTokenizer

tokenizer = BertTokenizer.from_pretrained("bert-base-uncased", max_length=1024)
model = BertModel.from_pretrained("bert-base-uncased")
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def preprocess_text(text):
    """
    Preprocesses a given text by removing URLs and tokenizing it using the BERT tokenizer.

    Parameters:
    text (str): The text to preprocess.

    Returns:
    token_ids (list of int): A list of token IDs, where each token corresponds to a word or a subword unit in the text after tokenization.
    """
    # Remove URLs
    text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "",
        text,
    )
    # Tokenize the text using the BERT tokenizer
    tokens = tokenizer.tokenize(text)

    # Convert tokens to IDs
    token_ids = tokenizer.convert_tokens_to_ids(tokens)

    return token_ids


def get_issue_embeddings(tokenized_issue_data, max_chunk_size=512):
    """
    Given tokenized issue data and a max chunk size, returns a dictionary of issue embeddings.
    Parameters:
    -----------
    tokenized_issue_data : dict
        A dictionary where keys are issue numbers and values are tokenized issue data.
    max_chunk_size : int
        The maximum chunk size for BERT embeddings. Default is 512.

    Returns:
    --------
    dict
        A dictionary where keys are issue numbers and values are corresponding embeddings.
    """
    tokenized_texts = list(tokenized_issue_data.values())
    issue_numbers = list(tokenized_issue_data.keys())

    def bert_embedding(text):
        """
        Given a text, returns the BERT embedding of the text.

        Parameters:
        text : str
            The text to get the BERT embedding for.

        Returns:
        np.ndarray
            The BERT embedding of the text.
        """
        if isinstance(text, list):
            text = text[0]
        token_ids = list(map(int, text.split()))

        if len(token_ids) < max_chunk_size:
            token_id_chunks = [token_ids]
        else:
            token_id_chunks = [
                token_ids[i : i + max_chunk_size]
                for i in range(0, len(token_ids), max_chunk_size)
            ]

        chunk_embeddings = []
        with torch.no_grad():
            for chunk in token_id_chunks:
                if not chunk:
                    continue
                embedding = (
                    model(torch.tensor(chunk).unsqueeze(0).to(device))[1]
                    .squeeze()
                    .cpu()
                    .numpy()
                )
                chunk_embeddings.append(embedding)
        avg_embedding = (
            np.zeros(768) if not chunk_embeddings else np.mean(chunk_embeddings, axis=0)
        )
        return avg_embedding

    issue_embeddings = {}
    for issue_number, text in zip(issue_numbers, tokenized_texts):
        embedding = bert_embedding(text)
        issue_embeddings[
            issue_number
        ] = embedding.tolist()  # Convert numpy array to list

    print(issue_embeddings)
    return issue_embeddings


from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)


def store_embeddings_in_milvus(issue_embeddings):
    """
    Store the issue embeddings in Milvus Vector Database.

    Args:
        issue_embeddings (dict): A dictionary where the keys are the issue numbers and the values are the embeddings.

    Returns:
        None
    """
    data_dict = issue_embeddings
    primary_keys = [key for key in data_dict.keys()]
    vectors = list(data_dict.values())

    if not vectors:
        print("No embeddings found. Exiting.")
        return

    dim = len(vectors[0])  # Set the dimension based on the length of the first vector

    # Connect to Milvus
    connections.connect("default", host="34.138.127.169", port="19530")

    # Check if collection exists
    if not utility.has_collection("my_collection"):
        # Create collection
        fields = [
            FieldSchema(
                name="pk", dtype=DataType.INT64, is_primary=True, auto_id=False
            ),
            FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]

        schema = CollectionSchema(
            fields, "My collection with primary keys and vector embeddings"
        )
        my_collection = Collection("my_collection", schema, consistency_level="Strong")

        # Create index
        index = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128},
        }
        my_collection.create_index("embeddings", index)
    else:
        my_collection = Collection("my_collection")

    # Load data into memory
    my_collection.load()

    # Fetch all records from the collection using primary key values
    existing_records = my_collection.query(
        f"pk in {primary_keys}", output_fields=["pk", "embeddings"]
    )

    # Create a dictionary to store existing records
    existing_dict = {
        int(record["pk"]): record["embeddings"] for record in existing_records
    }

    # Iterate over new embeddings and update or insert as necessary
    for pk, embedding in issue_embeddings.items():
        if pk in existing_dict:
            # Delete the old record
            my_collection.delete(f"pk in [{pk}]")
            my_collection.flush()

            # Insert the updated record
            entities = [[pk], [embedding]]
            insert_result = my_collection.insert(entities)
            my_collection.flush()
        else:
            # Insert the new embedding
            entities = [[pk], [embedding]]
            insert_result = my_collection.insert(entities)
            my_collection.flush()

    # Load data into memory
    my_collection.load()

    print("Done")


def fetch_and_store_github_issues(owner_repo_pairs, **kwargs):
    """
    This function fetches all issues from the GitHub repositories specified in owner_repo_pairs, stores them in Snowflake, and returns a list of the fetched issues.

    Parameters:

    owner_repo_pairs: a list of tuples representing owner and repository names (e.g. [("owner1", "repo1")])
    **kwargs: optional keyword arguments
    Returns:

    fetched_issues: a list of dictionaries representing the fetched issues
    """
    fetched_issues = []

    for owner, repo in owner_repo_pairs:
        issues = get_all_issues(owner, repo, access_token)
        store_issues_in_snowflake(issues, owner, repo)
        fetched_issues.extend(issues)

    print(fetched_issues)
    return fetched_issues


def compute_embeddings(fetched_issues, **kwargs):
    """Compute BERT embeddings for the fetched GitHub issues.

    Args:
        fetched_issues (list): A list of dictionaries containing information about GitHub issues.
        **kwargs: Other keyword arguments.

    Returns:
        None.
    """
    issue_ids = []
    issue_embeddings = {}

    for issue in fetched_issues:
        issue_number = issue["id"]
        body_text = issue["body"]
        preprocessed_text = preprocess_text(body_text)
        tokenized_text = " ".join([str(token_id) for token_id in preprocessed_text])

        embedding = get_issue_embeddings({issue_number: tokenized_text})
        issue_embeddings[int(issue_number)] = embedding[issue_number]

        issue_ids.append(issue_number)
        kwargs["ti"].xcom_push(key=str(issue_number), value=embedding[issue_number])

    kwargs["ti"].xcom_push(key="issue_ids", value=issue_ids)


def store_embeddings_in_milvus_task(**kwargs):
    """
    Retrieves computed embeddings from task instance XComs and stores them in a Milvus collection.

    :param kwargs: A dictionary of keyword arguments.
    """

    issue_ids = kwargs["ti"].xcom_pull(key="issue_ids")
    issue_embeddings = {}
    for issue_id in issue_ids:
        embedding = kwargs["ti"].xcom_pull(key=str(issue_id))
        issue_embeddings[int(issue_id)] = embedding  # Convert the issue to an integer
    store_embeddings_in_milvus(issue_embeddings)


fetch_owner_repo_pairs_task = PythonOperator(
    task_id="fetch_owner_repo_pairs",
    python_callable=get_owner_repo_pairs_from_snowflake,
    provide_context=True,
    dag=dag,
)

fetch_and_store_github_issues_task = PythonOperator(
    task_id="fetch_and_store_github_issues",
    python_callable=fetch_and_store_github_issues,
    op_args=[fetch_owner_repo_pairs_task.output],
    provide_context=True,
    dag=dag,
)

compute_embeddings_task = PythonOperator(
    task_id="compute_embeddings",
    python_callable=compute_embeddings,
    provide_context=True,
    op_args=[fetch_and_store_github_issues_task.output],
    dag=dag,
)

store_embeddings_in_milvus_task = PythonOperator(
    task_id="store_embeddings_in_milvus",
    python_callable=store_embeddings_in_milvus_task,
    provide_context=True,
    dag=dag,
)

(
    fetch_owner_repo_pairs_task
    >> fetch_and_store_github_issues_task
    >> compute_embeddings_task
    >> store_embeddings_in_milvus_task
)
