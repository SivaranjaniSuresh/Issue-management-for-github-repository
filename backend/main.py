import ast
import os
from datetime import datetime, timedelta
from typing import Union

import models
import schema
from database import SessionLocal, engine
from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from hashing import Hash
from jose import JWTError, jwt
from pymilvus import Collection, connections
from sqlalchemy.orm import Session

#####################################################################################################################################
## Environment Variables
#####################################################################################################################################

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))

#####################################################################################################################################
## FastAPI Initialization and Table Creation
#####################################################################################################################################

app = FastAPI()
models.Base.metadata.create_all(engine)


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


@app.get("/similar_issues", tags=["Github Issues"])
async def get_similar_issues(
    embedded_issue_text_dict: str,
    selected_owner: str,
    selected_repo: str,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(get_logged_in_user),
):
    embedded_issue_text_dict = ast.literal_eval(embedded_issue_text_dict)
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


@app.get("/github_search", tags=["Github Issues"])
async def get_similar_issues(
    embedded_issue_text_dict: str,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(get_logged_in_user),
):
    embedded_issue_text_dict = ast.literal_eval(embedded_issue_text_dict)
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
