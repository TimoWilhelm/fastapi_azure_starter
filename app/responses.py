from fastapi import status
from pydantic import BaseModel


class Detail(BaseModel):
    detail: str


class Error(BaseModel):
    error: str


unauthorized_response = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Unauthorized",
        "model": Detail,
    }
}

too_many_requests_response = {
    status.HTTP_429_TOO_MANY_REQUESTS: {
        "description": "Too many requests",
        "model": Error,
    },
}


default_responses = {
    **unauthorized_response,
    **too_many_requests_response,
}
