import streamlit as st
import requests
import json
import snowflake.connector
from dotenv import load_dotenv
import os
import datetime
import re
import re
import nltk
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from transformers import BertTokenizer, BertModel
import torch
from torch.nn import functional as F

nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download('omw-1.4')
load_dotenv()

SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")
SNOWFLAKE_TABLE = os.environ.get("SNOWFLAKE_TABLE")


access_token = os.environ.get("access_token")

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', max_length=1024)
model = BertModel.from_pretrained('bert-base-uncased')
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        table=SNOWFLAKE_TABLE
    )


def preprocess_text(text):
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    # Tokenize the text using the BERT tokenizer
    tokens = tokenizer.tokenize(text)

    # Convert tokens to IDs
    token_ids = tokenizer.convert_tokens_to_ids(tokens)
    
    return token_ids


def get_all_issues(owner, repo, access_token):
    cursor = conn.cursor()
    result = cursor.execute("SELECT MAX(UPDATED_AT) FROM GITHUB_ISSUES.PUBLIC.ISSUES")
    last_updated_at = result.fetchone()[0]
    # Increment last_updated_at by 1 second
    if last_updated_at is not None:
        last_updated_at = datetime.datetime.fromisoformat(last_updated_at.replace('Z', '+00:00'))
        last_updated_at += datetime.timedelta(seconds=1)
        last_updated_at = last_updated_at.isoformat().replace('+00:00', 'Z')
    
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"}
    issues = []
    page = 1
    per_page = 100

    while True:
        params = {"state": "all", "since":last_updated_at, "per_page": 100, "page": page}
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

                if comments_response.status_code == 200 and reactions_response.status_code == 200:
                    comments_data = comments_response.json()
                    reactions_data = reactions_response.json()
                    issue["comments"] = comments_data
                    issue["reactions"] = reactions_data
                    issues.append(issue)
                else:
                    print(f"Error fetching comments or reactions for issue {issue_number}")

        page += 1

    return issues

def store_issues_in_snowflake(issues, owner, repo):
    cursor = conn.cursor()

    for issue in issues:
        comments_dict = {}
        for comment in issue['comments']:
            comment_id = comment['id']
            comments_dict[f'comment {comment_id}'] = comment['body']

        comments_json = json.dumps(comments_dict)

        reactions_dict = []
        for reaction in issue["reactions"]:
            reaction_dict = {
                "id": reaction["id"],
                "user_login": reaction["user"]["login"],
                "user_id": reaction["user"]["id"],
                "content": reaction["content"],
                "created_at": reaction["created_at"]
            }
            reactions_dict.append(reaction_dict)

        reactions_json = json.dumps(reactions_dict)

        body = issue['body']
        issue_url = issue['html_url']
        assignees = ', '.join([assignee['login'] for assignee in issue['assignees']])
        labels = ', '.join([label['name'] for label in issue['labels']])
        milestone = issue['milestone']['title'] if issue['milestone'] else 'None'

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
        cursor.execute(query, {
            'id': issue['id'],
            'issue_url': issue_url,
            'repo_owner': owner,
            'repo_name': repo,
            'issue_number': issue['number'],
            'created_by': issue['user']['login'],
            'title': issue['title'],
            'body': body,
            'comments': comments_json,
            'reactions': reactions_json,
            'assignees': assignees,
            'labels': labels,
            'milestone': milestone,
            'state': issue['state'],
            'updated_at': issue['updated_at']
        })
        conn.commit()

    cursor.close()

def preprocess_closed_issue_data():
    cursor = conn.cursor()

    # Execute query to select all rows from the ISSUES table
    cursor.execute("SELECT * FROM GITHUB_ISSUES.PUBLIC.ISSUES WHERE STATE='closed' ORDER BY ISSUE_NUMBER")

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

    return preprocessed_texts

def preprocess_open_issue_data():
    cursor = conn.cursor()

    # Execute query to select all rows from the ISSUES table
    cursor.execute("SELECT * FROM GITHUB_ISSUES.PUBLIC.ISSUES WHERE STATE='open' ORDER BY ISSUE_NUMBER")

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

    return preprocessed_texts

def compute_similarity_faiss(tokenized_issue_data, tokenized_issue_text, max_chunk_size=512):
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
        issue_embeddings[issue_number] = embedding

    new_embedding = bert_embedding(tokenized_issue_text)

    embeddings = list(issue_embeddings.values())

    if new_embedding.shape != (768,) or any(embedding.shape != (768,) for embedding in embeddings):
        raise ValueError("Shape of embeddings is not (768,)")

    similarities = cosine_similarity([new_embedding], embeddings).flatten()

    similarity_percentages = [similarity * 100 for similarity in similarities]

    issue_similarity_list = list(zip(issue_numbers, similarity_percentages))

    issue_embeddings_list = {issue_number: ', '.join(map(str, embedding.tolist())) for issue_number, embedding in zip(issue_numbers, embeddings)}

    return issue_embeddings_list, issue_similarity_list

def get_issue_url(issue_number):
    cursor = conn.cursor()
    cursor.execute("SELECT ISSUE_URL FROM GITHUB_ISSUES.PUBLIC.ISSUES WHERE ID = %s", (issue_number,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return row[0]
    else:
        return None

tokenized_issue_text = []

def main():
    st.title("GitHub Issues to Snowflake")

    st.write("Enter the GitHub repository information and access token:")

    owner = st.text_input("Repository Owner")
    repo = st.text_input("Repository Name")
    issue_text = st.text_area("Enter the issue text to check similarity:")

    get_issues_button = st.button("Get Issues")
    if get_issues_button:
        with st.spinner("Retrieving issues..."):
            issues = get_all_issues(owner, repo, access_token)
            st.warning(f"Retrieved {len(issues)} issues.")

        with st.spinner("Storing issues in Snowflake..."):
            store_issues_in_snowflake(issues, owner, repo)
            st.success("Issues stored successfully in Snowflake.")

        with st.spinner("Pre-processing Closed Issue Data..."):
            tokenized_texts = preprocess_closed_issue_data()
            #st.write(tokenized_texts)

        with st.spinner("Pre-processing Open Issue Data..."):
            tokenized_texts_open = preprocess_open_issue_data()

        if issue_text:
            with st.spinner("Pre-processing Issue Text..."):
                preprocessed_issue_text = preprocess_text(issue_text)
                # Convert token IDs to strings and join them
                tokenized_text = ' '.join([str(token_id) for token_id in preprocessed_issue_text])
                tokenized_issue_text.append(tokenized_text)
                                
                #st.write(tokenized_issue_text)

            with st.spinner("Computing Similarity Scores..."):
                issue_embeddings, issue_similarity_list = compute_similarity_faiss(tokenized_texts, tokenized_issue_text)
                similar_issues = [(issue_number, similarity_percentage) for issue_number, similarity_percentage in issue_similarity_list if similarity_percentage > 98]
                for issue_number, similarity_percentage in similar_issues:
                    issue_url = get_issue_url(issue_number)
                    st.write(f"Issue Number {issue_number}: {similarity_percentage:.2f}% - {issue_url}")
                if not similar_issues:
                    with st.spinner("No similar closed issues found. Checking open issues..."):
                        issue_embeddings, issue_similarity_list_open = compute_similarity_faiss(tokenized_texts_open, tokenized_issue_text)
                        similar_issues_open = [(issue_number, similarity_percentage) for issue_number, similarity_percentage in issue_similarity_list_open if similarity_percentage > 90]
                        for issue_number, similarity_percentage in similar_issues_open:
                            issue_url = get_issue_url(issue_number)
                            st.write(f"Issue Number {issue_number}: {similarity_percentage:.2f}% - {issue_url}")

if __name__ == "__main__":
    main()
