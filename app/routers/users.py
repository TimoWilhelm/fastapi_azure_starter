from fastapi import APIRouter, Request, Response

from fastapi_azure_auth.user import User

from app import limiter
from app.logging import get_logger, get_tracer

logger = get_logger(__name__)

router = APIRouter()


@router.get("/me", tags=["users"])
@limiter.limit("5/minute")
async def get_user_me(request: Request, response: Response):
    with get_tracer().span(name="get_user_me"):
        user: User = request.state.user
        logger.info(f"User {user.claims.get('oid')} is requesting /me")
        return {"message": f"Hello {user.name}!"}
