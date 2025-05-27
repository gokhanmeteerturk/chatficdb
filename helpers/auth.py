"""
This module contains the authentication helper functions for the application.

Functions:
- validate_token: Validates the `Authorization` header to ensure the provided
token is in the correct format
  and matches the expected admin authentication token.

Dependencies:
- FastAPI: Used for raising HTTP exceptions.
- secrets: Provides secure comparison of tokens to prevent timing attacks.
- settings: Contains application-specific configurations, including the
 `ADMIN_AUTH_TOKEN`.

Usage:
This module is primarily used to validate API requests that require
admin-level authentication.
"""
import time
from secrets import compare_digest

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from fastapi import HTTPException, Header
from settings import ADMIN_AUTH_TOKEN, REGISTERED_PUBLIC_KEY_FILE, SERVER_METADATA

_loaded_public_key = None  # module-level cache

def get_bearer_token(authorization: str):
    if not str(authorization).startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    return str(authorization).split("Bearer ")[1]

def validate_admin_token(authorization: str = Header(..., convert_underscores=False)):
    token = get_bearer_token(authorization)
    # Validate the token
    return compare_digest(token, ADMIN_AUTH_TOKEN)

def _load_public_key_once():
    global _loaded_public_key
    if _loaded_public_key is None:
        with open(REGISTERED_PUBLIC_KEY_FILE, "rb") as f:
            pem_public_loaded = f.read()
        _loaded_public_key = load_pem_public_key(pem_public_loaded)
    return _loaded_public_key


def validate_and_decode_jwt_from_bearer(
    authorization: str = Header(..., convert_underscores=False)
):
    token = get_bearer_token(authorization)
    return validate_and_decode_jwt(token)

def validate_and_decode_jwt(jwt_token: str):
    loaded_public_key = _load_public_key_once()

    try:
        decoded = jwt.decode(
            jwt_token,
            key=loaded_public_key,
            algorithms=["EdDSA"],
            audience=SERVER_METADATA.get("slug")
        )
        print("\n✅ JWT verified! Payload:\n", decoded)
        return decoded
    except jwt.exceptions.ExpiredSignatureError as e:
        raise HTTPException(status_code=498, detail="Token has expired.")
    except jwt.exceptions.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token.")

from fastapi import HTTPException

def enforce_specific_username_or_admin(
        authorization: str,
        username: str | None
) -> None:
    """
    Raise HTTPException(401) unless the token is:
    - a valid admin token, OR
    - a valid JWT where sub == username.
    It will raise if not an admin and the username is None.
    """
    unauthorized = True
    if not validate_admin_token(authorization):
        jwt_decoded = validate_and_decode_jwt_from_bearer(authorization)
        if username is not None and jwt_decoded.get("sub") == username:
            unauthorized = False
    else:
        unauthorized = False

    if unauthorized:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing token"
        )

def enforce_and_extract_username_or_admin(authorization: str) -> str:
    """
    Require a valid token and return the identity:
    - "admin" if admin token
    - sub from JWT if user token
    - raise HTTPException(401) if token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required."
        )

    if validate_admin_token(authorization):
        return "admin"

    decoded = validate_and_decode_jwt_from_bearer(authorization)
    sub = decoded.get("sub")
    if not sub:
        raise HTTPException(
            status_code=401,
            detail="JWT is missing 'sub' claim"
        )

    return sub
