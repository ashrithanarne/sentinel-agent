#This file is for defining the structure of the tables (SQLalchemy declarative base to postgres tables)
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey,Text, JSON
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

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    problem_description = Column(String, nullable=False)
    status = Column(String, default="pending")   # pending, running, completed, step_limit_reached, failed
    answer = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class InvestigationStep(Base):
    __tablename__ = "investigation_steps"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    tool_name = Column(String, nullable=False)
    arguments = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    is_error = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())