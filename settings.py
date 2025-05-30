import os
from dotenv import load_dotenv

from helpers.utils import str_to_bool

CHATFICDB_VERSION_NAME = "v0.9.1"
CHATFICDB_VERSION_NUMBER = 901

load_dotenv()

S3_LINK = os.getenv('S3_LINK', "https://topaltdb.s3.us-east-2.amazonaws.com")

S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

ADMIN_AUTH_TOKEN = os.getenv("ADMIN_AUTH_TOKEN")

REGISTER_ON_STARTUP = False
SECRET_KEY = os.getenv('CHATFICDB_SECRET_KEY')

CHATFICLAB_BACKEND_URL = os.getenv('CHATFICLAB_BACKEND_URL',"https://api.chatficlab.com")
REGISTERED_PUBLIC_KEY_FILE = os.getenv('REGISTERED_PUBLIC_KEY_FILE',"/app/data/registered_key.pem")

SERVER_METADATA = {
    "name": os.getenv('SERVER_NAME'),
    "slug": os.getenv('SERVER_SLUG'),
    "url": os.getenv('SERVER_URL'),
    "nsfw": 1 if str_to_bool(os.getenv('SERVER_NSFW', 'False')) else 0,
    "submit_url": os.getenv('SUBMIT_URL'),
    "version": {
        "name": CHATFICDB_VERSION_NAME,
        "no": CHATFICDB_VERSION_NUMBER
    },
    "contact": {
        "name": os.getenv('CONTACT_NAME'),
        "url": os.getenv('CONTACT_URL'),
        "email": os.getenv('CONTACT_EMAIL'),
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
                'connect_timeout': 60,
                'minsize': 1,
                'maxsize': 10,
                'pool_recycle': 3600,  # Recycle connections after 1 hour
            }
        },
    },
    'apps': {
        'models': {
            'models': ["database.models", "aerich.models"],
            'default_connection': 'default',
        }
    }
}

DEBUG = str_to_bool(os.getenv('DEBUG', 'False'))

THEME = {
    'mode': os.getenv('THEME_MODE', 'light'),
    'primary': os.getenv('THEME_COLOR_PRIMARY', '#00AA8C'),
}

# STORIES ENDPOINT SETTINGS:
# Defines behaviour for single story endpoint.
# Defines "default" behaviour for stories endpoint.
SHOW_PUBLISHED_ONLY = str_to_bool(os.getenv('SHOW_PUBLISHED_ONLY', 'True'))
