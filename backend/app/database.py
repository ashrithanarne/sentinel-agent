#This file is about the connection components to the database
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL) #By default knows which database driver to use, It is a lazy setup(creates connection only after it is asked and keeps a pool of open connections after that)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #Asks engine for a connection from its pool and returns once done.
Base = declarative_base()

from app import models
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()