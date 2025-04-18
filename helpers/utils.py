import time
import random
import asyncio

import boto3
from botocore.config import Config


def create_s3_client():
    from settings import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        config=Config(
            region_name=AWS_REGION,
            signature_version='v4',
            retries={'max_attempts': 10, 'mode': 'standard'}
        ),
        region_name=AWS_REGION
    )

def str_to_bool(text):
    """
    Convert a string representation of a boolean value to its corresponding boolean value.

    Parameters:
        text (str): The string representation of the boolean value.

    Returns:
        bool: The corresponding boolean value.

    Raises:
        ValueError: If the string representation is not a valid boolean value.

    """
    if text.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif text.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ValueError



def getUniqueRandomStoryKey():
    hash_integers = str(int(time.time()))[::-1] + str(random.randint(0,9))
    # 0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h', 8: 'i', 9: 'j'
    hash_characters = ''.join(chr(ord('a') + int(char)) if bool(random.getrandbits(1)) else char for char in hash_integers)

    return hash_characters