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
from secrets import compare_digest

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from fastapi import HTTPException, Header
from settings import ADMIN_AUTH_TOKEN, REGISTERED_PUBLIC_KEY_FILE, SERVER_METADATA

_loaded_public_key = None  # module-level cache

def validate_token(authorization: str = Header(..., convert_underscores=False)):
    if not str(authorization).startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    # Extract the token part after "Bearer "
    token = str(authorization).split("Bearer ")[1]

    # Validate the token
    if not compare_digest(token, ADMIN_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    return True

def _load_public_key_once():
    global _loaded_public_key
    if _loaded_public_key is None:
        with open(REGISTERED_PUBLIC_KEY_FILE, "rb") as f:
            pem_public_loaded = f.read()
        _loaded_public_key = load_pem_public_key(pem_public_loaded)
    return _loaded_public_key

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
    except jwt.exceptions.InvalidTokenError as e:
        print("❌ JWT verification failed:", str(e))
        return None