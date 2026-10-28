from dataclasses import dataclass

from fastapi import Header, HTTPException, status
from supabase import Client, create_client

from app.config import get_settings


@dataclass
class CurrentUser:
    user_id: str
    db: Client  # Supabase client carrying the user's JWT, so Postgres RLS applies


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("Missing bearer token")

    settings = get_settings()
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

    try:
        response = client.auth.get_user(token)
    except Exception:
        raise _unauthorized("Invalid or expired token")
    if response is None or response.user is None:
        raise _unauthorized("Invalid or expired token")

    client.postgrest.auth(token)
    return CurrentUser(user_id=response.user.id, db=client)
