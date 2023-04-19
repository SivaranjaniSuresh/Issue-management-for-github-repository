from database import Base
from sqlalchemy import Column, DateTime, Integer, String


class User(Base):
    __tablename__ = "app_users"
    username = Column(String, primary_key=True)
    password = Column(String)
    credit_card = Column(String)
    service = Column(String)
    calls_remaining = Column(Integer)
