import os
import re
from datetime import datetime, timedelta
from typing import Dict, Union

import models
import numpy as np
import openai
import schema
import streamlit as st
import torch
from database import SessionLocal, engine
from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from hashing import Hash
from jose import JWTError, jwt
from pymilvus import Collection, connections
from sqlalchemy.orm import Session
from transformers import BertModel, BertTokenizer

#####################################################################################################################################
## Environment Variables
#####################################################################################################################################

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))

#####################################################################################################################################
## FastAPI Initialization, Model Loading and Table Creation
#####################################################################################################################################

app = FastAPI()
models.Base.metadata.create_all(engine)

tokenizer = BertTokenizer.from_pretrained(
    "./bert-base-uncased-tokenizer", max_length=1024
)

model = BertModel.from_pretrained("./bert-base-uncased")
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


###########################################################################################################################################
## Helper Functions
###########################################################################################################################################
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_username(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="signin")


def get_logged_in_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return get_username(token, credentials_exception)


def get_issue_url(issue_number, repo_owner=None, repo_name=None):
    session = SessionLocal()
    try:
        base_query = f"""SELECT ISSUE_URL, TITLE FROM GITHUB_ISSUES.PUBLIC.ISSUES 
            WHERE ID = '{issue_number}' AND STATE = 'closed'"""

        if repo_owner:
            base_query += f" AND REPO_OWNER = '{repo_owner}'"
        if repo_name:
            base_query += f" AND REPO_NAME = '{repo_name}'"

        result = session.execute(base_query)
        row = result.fetchone()
        return (row[0], row[1]) if row else (None, None)
    finally:
        session.close()


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


###########################################################################################################################################
## User API Endpoints
###########################################################################################################################################
@app.post("/signup", status_code=200, response_model=schema.ShowUser, tags=["Users"])
def signup(user: schema.User, db: Session = Depends(get_db)):
    existing_user = (
        db.query(models.User).filter(models.User.username == user.username).first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = models.User(
        username=user.username,
        password=Hash.bcrypt(user.password),
        credit_card=Hash.bcrypt(user.credit_card),
        service=user.service,
        calls_remaining=user.calls_remaining,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/signin", status_code=200, tags=["Users"])
def signin(
    request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = (
        db.query(models.User).filter(models.User.username == request.username).first()
    )
    if not user:
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    if not Hash.verify(user.password, request.password):
        raise HTTPException(status_code=400, detail="Invalid Password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


###########################################################################################################################################
## Github API Endpoints
###########################################################################################################################################


@app.post("/get_similar_issues/", tags=["Github Issues"])
async def get_similar_issues(
    request_data: Dict,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(get_logged_in_user),
):
    issue_body = request_data["issue_body"]
    selected_owner = request_data["selected_owner"]
    selected_repo = request_data["selected_repo"]

    embedded_issue_text_dict = get_embeddings(issue_body)
    similar_issues = check_similarity(embedded_issue_text_dict)
    similar_issues_output = []
    if similar_issues:
        for issue in similar_issues:
            issue_url, title = get_issue_url(issue["id"], selected_owner, selected_repo)
            if issue_url:
                similar_issues_output.append(
                    {
                        "title": title,
                        "id": issue["id"],
                        "similarity": issue["similarity"],
                        "url": issue_url,
                    }
                )
    if len(similar_issues_output) > 0:
        return similar_issues_output
    else:
        return "None LOL"


@app.post("/get_github_solutions/", tags=["Github Issues"])
async def get_github_solutions(
    request_data: Dict,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(get_logged_in_user),
):
    user_input = request_data["user_input"]

    embedded_issue_text_dict = get_embeddings(user_input)
    similar_issues = check_similarity(embedded_issue_text_dict)
    similar_issues_output = []
    if similar_issues:
        for issue in similar_issues:
            issue_url, title = get_issue_url(issue["id"])
            if issue_url:
                similar_issues_output.append(
                    {
                        "title": title,
                        "id": issue["id"],
                        "similarity": issue["similarity"],
                        "url": issue_url,
                    }
                )
    if len(similar_issues_output) > 0:
        return similar_issues_output
    else:
        return "None LOL"


###########################################################################################################################################
## Github - OpenAI Prompt Engineering
###########################################################################################################################################
@app.post("/get_issue_summary/", tags=["OpenAI-Github"])
async def get_summary(
    request_data: Dict,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(get_logged_in_user),
):
    text = request_data["text"]
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


@app.post("/get_possible_solution/", tags=["OpenAI-Github"])
async def get_possible_solution(
    request_data: Dict,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(get_logged_in_user),
):
    text = request_data["text"]
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
