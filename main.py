# main.py
import os
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Header
from dotenv import load_dotenv
import mysql.connector
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from email_validator import validate_email, EmailNotValidError
import bcrypt
app = FastAPI()
import logging

logging.basicConfig(level=logging.INFO)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from settings import DATABASE_SETTINGS

load_dotenv()

app = FastAPI()

# Connect to the database
def get_db():
    return mysql.connector.connect(**DATABASE_SETTINGS)

def get_story_from_db(storyGlobalId):
    db_connection = get_db()
    cursor = db_connection.cursor(dictionary=True)

    select_query = "SELECT * FROM stories WHERE storyGlobalId=%s LIMIT 1"
    values = (storyGlobalId,)

    try:
        cursor.execute(select_query, values)
        items = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Error connecting DB")
    finally:
        cursor.close()
        db_connection.close()

    if items is not None and len(items) > 0:
        item = items[0]
        return {
            "isFound": True,
            "title": item["title"],
            "description": item["description"],
            "author": item["author"],
            "patreonusername": item["patreonusername"],
            "cdn":"https://chatficdottop.s3.us-east-2.amazonaws.com"
            }
    else:
        raise HTTPException(status_code=404, detail="Story not found")

@app.get("/story")
def get_server(storyGlobalId: str):
    try:
        return get_story_from_db(storyGlobalId)
    except Exception as e:
        logging.error(e)
        return {"isFound": False,"title": "","description": "","author": "","patreonusername": "", "cdn":""}
