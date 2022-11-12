from fastapi.security import SecurityScopes
from fastapi.security.base import SecurityBase
from starlette.requests import Request

from app.packages.auth.user import User


class MockSecurity(SecurityBase):
    def __init__(self, scopes: list[str] = None):
        self.scopes = scopes

    async def init(self):
        pass

    def __call__(self, request: Request, security_scopes: SecurityScopes):
        user = User(
            name="Mock User",
            access_token="mock_access_token",
            claims={
                "sub": "mock_sub",
                "oid": "mock_oid",
                "scp": " ".join(self.scopes),
            },
        )
        request.state.user = user
        return user
