# settings.py
import os
from dotenv import load_dotenv

from helpers.utils import str_to_bool

CHATFICDB_VERSION_NAME = "v0.9.0"
CHATFICDB_VERSION_NUMBER = 900

load_dotenv()

SERVER_METADATA = {
    "name": os.getenv('SERVER_NAME'),
    "slug": os.getenv('SERVER_SLUG'),
    "url": os.getenv('SERVER_URL'),
    "nsfw": 1 if str_to_bool(os.getenv('SERVER_NSFW', 'False')) else 0,
    "submit_url": os.getenv('SUBMIT_URL'),
    "version": {
        "name": CHATFICDB_VERSION_NAME,
        "no": CHATFICDB_VERSION_NUMBER
    }
}

DATABASE_SETTINGS = {
    "user": os.getenv("DATABASE_USER"),
    "password": os.getenv("DATABASE_PASSWORD"),
    "host": os.getenv("DATABASE_HOST"),
    "database": os.getenv("DATABASE_NAME"),
    "port": int(os.getenv("DATABASE_PORT")),
}

TORTOISE_CONFIG = {
    'connections': {
        # Dict format for connection
        'default': {
            'engine': 'tortoise.backends.mysql',
            'credentials': {
                'host': DATABASE_SETTINGS.get('host'),
                'port': DATABASE_SETTINGS.get('port'),
                'user': DATABASE_SETTINGS.get('user'),
                'password': DATABASE_SETTINGS.get('password'),
                'database': DATABASE_SETTINGS.get('database'),
            }
        },
    },
    'apps': {
        'models': {
            'models': ["database.models", "aerich.models"],
            # If no default_connection specified, defaults to 'default'
            'default_connection': 'default',
        }
    }
}

DEBUG = str_to_bool(os.getenv('DEBUG', 'False'))

THEME = {
    'mode': os.getenv('THEME_MODE', 'light'),
    'primary': os.getenv('THEME_COLOR_PRIMARY', '#00AA8C'),
}