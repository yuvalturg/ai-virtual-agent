"""
Keycloak JWT authentication for FastAPI.

This module provides JWT token validation against Keycloak OIDC provider.
"""

import logging
import os
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from keycloak import KeycloakOpenID

logger = logging.getLogger(__name__)

# Keycloak configuration from environment
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "ai-virtual-agent")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "ai-virtual-agent")

# Initialize Keycloak OpenID client
keycloak_openid = None


def get_keycloak_client() -> KeycloakOpenID:
    """Get or initialize Keycloak OpenID client."""
    global keycloak_openid
    if keycloak_openid is None:
        keycloak_openid = KeycloakOpenID(
            server_url=KEYCLOAK_URL,
            client_id=KEYCLOAK_CLIENT_ID,
            realm_name=KEYCLOAK_REALM,
        )
    return keycloak_openid


def get_public_key() -> str:
    """Fetch the public key from Keycloak for JWT validation."""
    try:
        client = get_keycloak_client()
        return (
            "-----BEGIN PUBLIC KEY-----\n"
            + client.public_key()
            + "\n-----END PUBLIC KEY-----"
        )
    except Exception as e:
        logger.error(f"Failed to fetch Keycloak public key: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


def validate_token(token: str) -> dict:
    """
    Validate JWT token from Keycloak.

    Args:
        token: JWT access token

    Returns:
        dict: Decoded token payload containing user info and claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Get public key from Keycloak
        public_key = get_public_key()

        # Decode and validate token
        options = {
            "verify_signature": True,
            "verify_aud": False,  # Audience claim not always present
            "verify_exp": True,
        }

        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options=options,
        )

        logger.debug(f"Token validated for user: {decoded_token.get('preferred_username')}")
        return decoded_token

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_user_info(token_payload: dict) -> dict:
    """
    Extract user information from decoded JWT token.

    Args:
        token_payload: Decoded JWT token payload

    Returns:
        dict: User information with keys: username, email, role
    """
    # Extract username (Keycloak uses 'preferred_username')
    username = token_payload.get("preferred_username") or token_payload.get("sub")

    # Extract email
    email = token_payload.get("email", f"{username}@unknown")

    # Extract roles from realm_access
    realm_access = token_payload.get("realm_access", {})
    roles = realm_access.get("roles", [])

    # Determine highest role (admin > devops > user)
    role = "user"  # Default role
    if "admin" in roles:
        role = "admin"
    elif "devops" in roles:
        role = "devops"

    logger.info(f"Extracted user info - username: {username}, email: {email}, role: {role}")

    return {
        "username": username,
        "email": email,
        "role": role,
    }


def get_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        str: JWT token or None if not found
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]
