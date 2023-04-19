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


###########################################################################################################################################
## User API Endpoints
###########################################################################################################################################
@app.post("/signup", status_code=200, response_model=schema.ShowUser, tags=["user"])
def signup(user: schema.User, db: Session = Depends(get_db)):
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


@app.post("/signin", status_code=200, tags=["user"])
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
