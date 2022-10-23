from pydantic import BaseModel

from fastapi import APIRouter, Request, Response, status

from fastapi_azure_auth.user import User

from app import limiter
from app.logging import get_logger, get_tracer

logger = get_logger(__name__)

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
                "application/json": {
                    "example": {
                        "greeting": "Hello John Doe!"
                    }
                }
            },
        },
    }
)
@limiter.limit("5/minute")
async def get_user_me(request: Request, response: Response):
    with get_tracer().span(name="get_user_me"):
        user: User = request.state.user
        logger.info(f"User {user.claims.get('oid')} is requesting /me")
        return Greeting(greeting=f"Hello {user.claims.get('name')}!")
