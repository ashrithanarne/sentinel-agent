#This file is for defining the structure of the tables
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    full_name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    default_branch = Column(String, nullable=True)
    private = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 