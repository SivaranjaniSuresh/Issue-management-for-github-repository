import datetime

from database import Base
from sqlalchemy import Column, DateTime, Integer, Sequence, String


class User(Base):
    __tablename__ = "APP_USERS"
    username = Column(String, primary_key=True)
    password = Column(String)
    credit_card = Column(String)
    service = Column(String)
    calls_remaining = Column(Integer)


class UserActivity(Base):
    __tablename__ = "LOGS"
    id = Column(
        Integer, Sequence("user_activity_id_seq"), primary_key=True, autoincrement=True
    )
    username = Column(String(255), nullable=False)
    request_type = Column(String(10), nullable=False)
    api_endpoint = Column(String(255), nullable=False)
    response_code = Column(Integer, nullable=False)
    description = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
