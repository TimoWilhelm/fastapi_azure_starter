from fastapi import Request
from slowapi import Limiter

from app.config import get_settings
from app.packages.auth import User


def key_func(request: Request) -> str:
    user: User | None = getattr(request.state, "user", None)

    if user is not None:
        user_id = user.claims.get("sub")
        if isinstance(user_id, str) and user_id != "":
            return user_id

    if request.client is not None:
        return request.client.host

    return ""


settings = get_settings()

limiter = Limiter(
    key_func=key_func,
    default_limits=["100/minute"],
    headers_enabled=True,
    storage_uri=settings.REDIS_CONNECTION_STRING or "memory://",
)
