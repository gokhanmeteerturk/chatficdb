# settings.py
import os
from dotenv import load_dotenv

from helpers.utils import str_to_bool

load_dotenv()

SITE_METADATA = {
    "name": os.getenv('SERVER_NAME'),
    "slug": os.getenv('SERVER_SLUG'),
    "url": os.getenv('SERVER_URL'),
    "nsfw": str_to_bool(os.getenv('SERVER_NSFW', 'False'))
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
