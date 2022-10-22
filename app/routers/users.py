from fastapi import APIRouter, Request, Response

from fastapi_azure_auth.user import User

from app import limiter

router = APIRouter()


@router.get("/me", tags=["users"])
@limiter.limit("5/minute")
async def get_user_me(request: Request, response: Response):
    user: User = request.state.user
    return {"message": f"Hello {user.name}!"}
