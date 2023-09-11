from fastapi.security import SecurityScopes
from fastapi.security.base import SecurityBase
from starlette.requests import Request

from app.packages.auth.user import User


class MockSecurity:
    @classmethod
    def init(cls, tenant_id: str, client_id: str):
        pass

    @classmethod
    @property
    def instance(cls):
        return MockSecurityBase()


class MockSecurityBase(SecurityBase):
    def __call__(self, request: Request, security_scopes: SecurityScopes):
        claims = {
            "aud": "mock_aud",
            "tid": "mock_tid",
            "roles": ["mock_role"],
            "sub": "mock_sub",
            "oid": "mock_oid",
            "scp": "mock_scp",
            "name": "Mock User",
        }

        user = User(
            aud=claims["aud"],
            tid=claims["tid"],
            roles=claims["roles"],
            claims=claims,
            scp=claims["scp"],
            name=claims["name"],
            access_token="mock_access_token",
        )
        request.state.user = user
        return user
