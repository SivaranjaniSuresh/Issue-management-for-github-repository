from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field


class User(BaseModel):
    username: str
    password: str
    credit_card: str
    service: str
    calls_remaining: int


class ShowUser(BaseModel):
    username: str

    class Config:
        orm_mode = True
