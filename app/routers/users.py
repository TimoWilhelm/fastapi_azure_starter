import logging

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel

from app.limiter import RateLimit
from app.packages.auth import User
from app.packages.auth.dependencies import RoleValidator, get_required_user

logger = logging.getLogger(__name__)

router = APIRouter()


class Greeting(BaseModel):
    greeting: str


@router.get(
    "/greet",
    name="Greet Me",
    description="Greets the currently signed-in user.",
    response_model=Greeting,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {"example": {"greeting": "Hello John Doe!"}}
            },
        },
    },
)
@RateLimit.instance().limit("10/minute")
async def get_greeting(
    request: Request, response: Response, user: User = Depends(get_required_user)
):
    logger.info(f"User {user.claims.get('oid')} is requesting a greeting.")
    return Greeting(greeting=f"Hello {user.claims.get('name')}!")


@router.get(
    "/admin",
    dependencies=[Depends(RoleValidator(["admin"]))],
    name="Admin Endpoint",
    response_model=str,
)
async def get_admin(request: Request, response: Response):
    return "You are an admin!"
