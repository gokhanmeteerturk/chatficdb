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
from fastapi import HTTPException, Header
from settings import ADMIN_AUTH_TOKEN


def validate_token(authorization: str = Header(..., convert_underscores=False)):
    if not str(authorization).startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    # Extract the token part after "Bearer "
    token = str(authorization).split("Bearer ")[1]

    # Validate the token
    if not compare_digest(token, ADMIN_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    return True
