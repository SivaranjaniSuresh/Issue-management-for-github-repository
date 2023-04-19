import os
import re

import numpy as np
import requests
import streamlit as st
import torch
from dotenv import load_dotenv
from pymilvus import Collection, connections
from transformers import BertModel, BertTokenizer

from backend.database import SessionLocal

load_dotenv()

GITHUB_ACCESS_TOKEN = os.environ.get("access_token")

tokenizer = BertTokenizer.from_pretrained("bert-base-uncased", max_length=1024)
model = BertModel.from_pretrained("bert-base-uncased")
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


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


def get_issue_url(issue_number, repo_owner, repo_name):
    session = SessionLocal()
    try:
        result = session.execute(
            "SELECT ISSUE_URL FROM GITHUB_ISSUES.PUBLIC.ISSUES "
            "WHERE ID = :issue_number AND REPO_OWNER = :repo_owner AND REPO_NAME = :repo_name",
            {
                "issue_number": issue_number,
                "repo_owner": repo_owner,
                "repo_name": repo_name,
            },
        )
        row = result.fetchone()
        return row[0] if row else None
    finally:
        session.close()


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


def get_unique_owner_repo_pairs():
    session = SessionLocal()
    result = session.execute(
        "SELECT DISTINCT REPO_OWNER, REPO_NAME FROM GITHUB_ISSUES.PUBLIC.ISSUES"
    )
    unique_pairs = result.fetchall()
    return unique_pairs


def get_issue_comments(issue_url, access_token):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {access_token}",
    }
    response = requests.get(issue_url + "/comments", headers=headers)

    if response.status_code == 200:
        comments = response.json()
        return comments
    else:
        print(f"Error {response.status_code}: Failed to fetch comments")
        return []


def get_open_issues(owner, repo, access_token, page, per_page=10):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {"state": "open", "page": page, "per_page": per_page}
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {access_token}",
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        issues = response.json()
        # Fetch comments for each issue
        for issue in issues:
            issue["comments_data"] = get_issue_comments(
                issue["comments_url"], access_token
            )
        return issues
    else:
        print(f"Error {response.status_code}: Failed to fetch issues")
        return []


def get_similar_issues(issue_text, selected_owner, selected_repo):
    tokenized_issue_text = []
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
            i: list(embedding) for i, embedding in enumerate(embedded_issue_text)
        }

    with st.spinner("Checking Similarity..."):
        similar_issues = check_similarity(embedded_issue_text_dict)
        if similar_issues:
            st.warning(
                "Similar issues with more than 98% similarity and state='closed':"
            )
            for issue in similar_issues:
                issue_url = get_issue_url(issue["id"], selected_owner, selected_repo)
                if issue_url:
                    st.success(
                        f"Issue ID: {issue['id']}: {issue['similarity']}% - {issue_url}"
                    )
        else:
            st.error(f"No similar issue found")


def issuesearch(token, user_id):
    st.title("GitHub Issues Similarity Check")
    col1, col2 = st.columns(2)
    ## Get All Repo Owner
    unique_pairs = get_unique_owner_repo_pairs()
    ## Create a dictionary with owner names as keys and lists of repos as values
    owner_repo_dict = {}
    for owner, repo in unique_pairs:
        if owner not in owner_repo_dict:
            owner_repo_dict[owner] = []
        owner_repo_dict[owner].append(repo)

    # Dropdown for selecting an owner
    selected_owner = col1.selectbox("Select an owner", list(owner_repo_dict.keys()))

    # Dropdown for selecting a repository
    if selected_owner:
        selected_repo = col2.selectbox(
            "Select a repository", owner_repo_dict[selected_owner]
        )

    # Pagination
    page = st.number_input("Page", min_value=1, value=1, step=1)

    # Fetch and display open issues
    issues = get_open_issues(selected_owner, selected_repo, GITHUB_ACCESS_TOKEN, page)
    if issues:
        st.write(f"**Open Issues for {selected_owner}/{selected_repo} (Page {page}):**")
        for issue in issues:
            issue_title = issue["title"]
            issue_body = issue["body"]
            issue_comments = issue["comments_data"]

            with st.expander(issue_title):
                st.write(issue_body)
                st.write("Comments:")
                if issue_comments:
                    for comment in issue_comments:
                        st.write(comment["user"]["login"] + ":")
                        st.write(comment["body"])
                else:
                    st.write("No comments.")

                # Button to check for similar issues
                if st.button(f"Find similar issues for {issue_title}"):
                    similar_issues = get_similar_issues(
                        issue_body, selected_owner, selected_repo
                    )
                    if similar_issues:
                        st.write("Similar issues:")
                        for sim_issue in similar_issues:
                            st.write(f"{sim_issue['title']} - {sim_issue['html_url']}")
                    else:
                        st.write("No similar issues found.")
    else:
        st.write("No open issues found.")


if __name__ == "__main__":
    issuesearch()
