import os
import re

import numpy as np
import snowflake.connector
import streamlit as st
import torch
from dotenv import load_dotenv
from pymilvus import Collection, connections
from transformers import BertModel, BertTokenizer

load_dotenv()

SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")
SNOWFLAKE_TABLE = os.environ.get("SNOWFLAKE_TABLE")

access_token = os.environ.get("access_token")

tokenizer = BertTokenizer.from_pretrained("bert-base-uncased", max_length=1024)
model = BertModel.from_pretrained("bert-base-uncased")
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


conn = snowflake.connector.connect(
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    account=SNOWFLAKE_ACCOUNT,
    warehouse=SNOWFLAKE_WAREHOUSE,
    database=SNOWFLAKE_DATABASE,
    schema=SNOWFLAKE_SCHEMA,
    table=SNOWFLAKE_TABLE,
)


def preprocess_text(text):
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


def bert_embedding(text):
    max_chunk_size = 512
    embedded_text = []
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
    embedded_text.append(avg_embedding)
    return embedded_text


def get_issue_url(issue_number):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ISSUE_URL FROM GITHUB_ISSUES.PUBLIC.ISSUES WHERE ID = %s",
        (issue_number,),
    )
    row = cursor.fetchone()
    cursor.close()
    if row:
        return row[0]
    else:
        return None


tokenized_issue_text = []


def check_similarity(embedded_issue):
    # Connect to Milvus
    connections.connect(alias="default", host="34.138.127.169", port="19530")
    collection_name = "my_collection"
    collection = Collection(name=collection_name)
    search_vector = list(embedded_issue.values())[0]
    top_k = 999
    anns_field = "embeddings"
    search_params = {"metric_type": "L2", "params": {"nprobe": 9999}}

    results = collection.search(
        data=[search_vector], anns_field=anns_field, param=search_params, limit=top_k
    )

    max_dist = 0
    filtered_results = []

    for result in results:
        for match in result:
            max_dist = max(match.distance, max_dist)

    for result in results:
        for match in result:
            similarity = ((max_dist - match.distance) / max_dist) * 100
            # Round the similarity score to 2 decimal places
            similarity = round(similarity, 2)
            if similarity > 80:
                filtered_results.append({"id": match.id, "similarity": similarity})

    return filtered_results


def issuesearch(token, user_id):
    st.title("GitHub Issues Similarity Check")
    issue_text = st.text_area("Enter the issue text to check similarity:")

    get_issues_button = st.button("Check Similarity")
    if get_issues_button:
        if issue_text:
            with st.spinner("Pre-processing Issue Text..."):
                preprocessed_issue_text = preprocess_text(issue_text)
                # Convert token IDs to strings and join them
                tokenized_text = " ".join(
                    [str(token_id) for token_id in preprocessed_issue_text]
                )
                tokenized_issue_text.append(tokenized_text)

            with st.spinner("Embedding Issue Text..."):
                embedded_issue_text = bert_embedding(tokenized_issue_text)
                embedded_issue_text_dict = {
                    i: list(embedding)
                    for i, embedding in enumerate(embedded_issue_text)
                }

            with st.spinner("Checking Similarity..."):
                similar_issues = check_similarity(embedded_issue_text_dict)
                if similar_issues:
                    st.warning(
                        "Similar issues with more than 98% similarity and state='closed':"
                    )
                    for issue in similar_issues:
                        issue_url = get_issue_url(issue["id"])
                        if issue_url:
                            st.success(
                                f"Issue ID: {issue['id']}: {issue['similarity']}% - {issue_url}"
                            )
                else:
                    st.error(f"No similar issue found")


if __name__ == "__main__":
    issuesearch()
