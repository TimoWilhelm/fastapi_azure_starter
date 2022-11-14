from functools import cache

from fastapi import Request
from slowapi import Limiter

from app.packages.auth import User


def _key_func(request: Request) -> str:
    user: User | None = getattr(request.state, "user", None)

    if user is not None:
        user_id = user.claims.get("sub")
        if isinstance(user_id, str) and user_id != "":
            return user_id

    if request.client is not None:
        return request.client.host

    return ""


class RateLimit:
    _limiter: Limiter | None = None

    @classmethod
    def init(
        cls, redis_connection_string: str | None, default_limit: str = "100/minute"
    ):
        cls._limiter = Limiter(
            key_func=_key_func,
            default_limits=[default_limit],
            headers_enabled=True,
            storage_uri=redis_connection_string or "memory://",
        )

        return cls._limiter

    @classmethod
    @cache
    def instance(cls):
        if cls._limiter is None:  # pragma: no cover
            raise RuntimeError("RateLimit not initialized")
        return cls._limiter
