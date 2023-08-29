# settings.py
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_SETTINGS = {
    'user': os.getenv("DATABASE_USER"),
    'password': os.getenv("DATABASE_PASSWORD"),
    'host': os.getenv("DATABASE_HOST"),
    'database': os.getenv("DATABASE_NAME"),
    'port': int(os.getenv("DATABASE_PORT")),
}

DEBUG = os.getenv("DEBUG") == "True"
