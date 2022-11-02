from typing import Any

from pydantic import BaseModel, Field


class User(BaseModel):
    aud: str = Field(..., description="Audience")
    tid: str = Field(..., description="Tenant ID")
    roles: list[str] = Field(
        default=[], description="Roles (Groups) the user has for this app"
    )
    claims: dict[str, Any] = Field(..., description="The entire decoded token")
    scp: str | None = Field(default=None, description="Scope")
    name: str | None = Field(default=None, description="Name")
    access_token: str = Field(
        ..., description="The access_token. Can be used for fetching the Graph API"
    )
