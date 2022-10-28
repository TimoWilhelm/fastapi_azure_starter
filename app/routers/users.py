import logging

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel

from app import limiter
from app.packages.security import User
from app.packages.security.dependencies import RoleValidator
from app.util.tracing import get_span

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
@limiter.limit("5/minute")
async def get_greeting(request: Request, response: Response):
    with get_span(name="get_greeting"):
        user: User = request.state.user
        logger.info(f"User {user.claims.get('oid')} is requesting a greeting.")
        return Greeting(greeting=f"Hello {user.claims.get('name')}!")


@router.get(
    "/admin",
    dependencies=[Depends(RoleValidator(["admin"]))],
    name="Admin Endpoint",
    response_model=str,
)
async def get_admin(request: Request, response: Response):
    with get_span(name="get_user_me"):
        return "You are an admin!"
