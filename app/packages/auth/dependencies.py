from typing import List

from fastapi import Request

from .exceptions import InvalidAuthException


class RoleValidator:
    def __init__(self, roles: List[str]):
        self.roles = roles

    def __call__(self, request: Request):
        user = getattr(request.state, "user", None)

        if user is None:
            raise InvalidAuthException("No user attached to request")

        user_roles = user.claims.get("roles", [])

        if not isinstance(user_roles, list):
            raise InvalidAuthException("Invalid formatted roles claim")

        if not any(role in user_roles for role in self.roles):
            raise InvalidAuthException("Insufficient permissions")

        return user_roles
