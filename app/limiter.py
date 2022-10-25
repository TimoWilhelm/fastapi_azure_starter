from typing import Optional

from fastapi import Request

from slowapi import Limiter

from app import settings
from app.security import User


def key_func(request: Request) -> str:
    user: Optional[User] = request.state.user
    if user is not None:
        return str(user.claims.get('oid') or user.claims.get('sub'))

    if (request.client is not None):
        return request.client.host

    return "default"


limiter = Limiter(
    key_func=key_func,
    default_limits=["100/minute"],
    headers_enabled=True,
    storage_uri=settings.REDIS_CONNECTION_STRING or "memory://",
)
