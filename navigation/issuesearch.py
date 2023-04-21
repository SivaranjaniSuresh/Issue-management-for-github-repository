import json
import os
import re

import numpy as np
import openai
import requests
import streamlit as st
import torch
from dotenv import load_dotenv
from pymilvus import Collection, connections
from transformers import BertModel, BertTokenizer

from backend.database import SessionLocal

load_dotenv()

GITHUB_ACCESS_TOKEN = os.environ.get("access_token")
openai.api_key = os.environ.get("OPENAI_API_KEY")
PREFIX = os.environ.get("PREFIX")

tokenizer = BertTokenizer.from_pretrained(
    "./bert-base-uncased-tokenizer", max_length=1024
)
model = BertModel.from_pretrained("./bert-base-uncased")

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
            if similarity > 90:
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


def get_embeddings(issue_text):
    tokenized_issue_text = []
    with st.spinner("Pre-processing Issue Text..."):
        preprocessed_issue_text = preprocess_text(issue_text)
        tokenized_text = " ".join(
            [str(token_id) for token_id in preprocessed_issue_text]
        )
        tokenized_issue_text.append(tokenized_text)

    with st.spinner("Embedding Issue Text..."):
        embedded_issue_text = bert_embedding(tokenized_issue_text)
        embedded_issue_text_dict = {
            i: list(embedding) for i, embedding in enumerate(embedded_issue_text)
        }
    return embedded_issue_text_dict


def get_summary(text):
    prompt = f"Please analyze the following GitHub issue body and provide a brief and concise summary of the problem. Please note that we are only looking for a summary and not a solution or any additional information. Thank you. ONLY SUMMARY.\n\nIssue Body: {text}\n\n"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.6,
    )
    return response.choices[0].message["content"].strip()


def get_possible_solution(text):
    prompt = f"What is a possible solution to the following GitHub issue? Please provide a detailed solution, or if there are no questions to answer in the issue, suggest some potential solutions or explain why a solution may not be feasible. If you are unsure, please provide any insights or suggestions that may be helpful in resolving the issue. Thank you for your contribution!.\n\n Github Issue:{text}\n\n"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.6,
    )
    return response.choices[0].message["content"].strip()


def issuesearch(access_token, user_id):
    headers = {"Authorization": f"Bearer {access_token}"}

    st.title("GitHub Issues Similarity Check")
    col1, col2 = st.columns(2)
    unique_pairs = get_unique_owner_repo_pairs()
    owner_repo_dict = {}
    for owner, repo in unique_pairs:
        if owner not in owner_repo_dict:
            owner_repo_dict[owner] = []
        owner_repo_dict[owner].append(repo)

    selected_owner = col1.selectbox("Select an owner", list(owner_repo_dict.keys()))

    if selected_owner:
        selected_repo = col2.selectbox(
            "Select a repository", owner_repo_dict[selected_owner]
        )

    page = st.number_input("Page", min_value=1, value=1, step=1)

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

                summary_key = f"summary_{issue['number']}"
                if st.session_state.get(summary_key):
                    st.markdown(
                        f"<div style='border: 1px solid #404040; padding: 10px; border-radius: 10px;'><h4>Summary</h4>{st.session_state[summary_key]}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(
                        "Reveal the Essence.", key=f"summary_button_{issue['number']}"
                    ):
                        with st.spinner("Generating summary..."):
                            summary = get_summary(issue_body)
                            st.session_state[summary_key] = summary
                            st.markdown(
                                f"<div style='border: 1px solid #404040; padding: 10px; border-radius: 10px;'><h4>Summary</h4>{summary}</div>",
                                unsafe_allow_html=True,
                            )
                            st.experimental_rerun()

                if st.button(f"Find similar issues for {issue_title}"):
                    embeddings = get_embeddings(issue_body)
                    response = requests.get(
                        f"{PREFIX}/similar_issues",
                        params={
                            "embedded_issue_text_dict": str(embeddings),
                            "selected_owner": selected_owner,
                            "selected_repo": selected_repo,
                        },
                        headers=headers,
                    )
                    if response.status_code == 200:
                        similar_issues = response.json()
                    else:
                        st.write(f"Error: {response.status_code}")
                        similar_issues = "None LOL"
                    if similar_issues != "None LOL" and similar_issues != []:
                        similar_issues_html = "<div style='border: 1px solid #404040; padding: 10px; border-radius: 10px;'><h4>Similar Issues</h4>"
                        for similar_issue in similar_issues:
                            title = similar_issue["title"]
                            issue_id = similar_issue["id"]
                            similarity = similar_issue["similarity"]
                            similarity_html = f"<span style='color: #39FF14;'>{similarity:.2f}%</span>"
                            url = similar_issue["url"]
                            link_text = f"({url})"
                            link_html = f"<a href='{url}'>{link_text}</a>"
                            issue_html = f"<p>- {title} (#{issue_id}) - {similarity_html} - {link_html}</p>"
                            similar_issues_html += issue_html
                        similar_issues_html += "</div>"
                        st.markdown(similar_issues_html, unsafe_allow_html=True)
                    else:
                        st.error("No similar closed issue found.")
                        possible_solution = get_possible_solution(issue_body)
                        if possible_solution:
                            possible_solution_html = "<div style='border: 1px solid #404040; padding: 10px; border-radius: 10px;'><h4>Possible Solution</h4>"
                            possible_solution_html += f"<p>{possible_solution}</p>"
                            possible_solution_html += "</div>"
                            st.markdown(possible_solution_html, unsafe_allow_html=True)
    else:
        st.write("No issues found.")


if __name__ == "__main__":
    issuesearch()
