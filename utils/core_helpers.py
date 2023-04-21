from jose import JWTError, jwt
import re
from transformers import BertModel, BertTokenizer
import torch
import requests
import openai
import numpy as np
import streamlit as st

tokenizer = BertTokenizer.from_pretrained(
    "bert-base-uncased", max_length=1024
)
model = BertModel.from_pretrained("bert-base-uncased")

model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def decode_token(token, SECRET_KEY, ALGORITHM):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        return None
    
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

def get_unique_owner_repo_pairs(session):
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
    response = requests.get(issue_url, headers=headers)
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
