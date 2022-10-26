from fastapi import HTTPException, status


class NotInitializedException(Exception):
    """
    Exception raised when the security module is not initialized.
    """

    def __init__(
        self,
        message="Security module not initialized. Did you forget to init() on application startup?",
    ):
        super(NotInitializedException, self).__init__(message)
        self.message = message


class InvalidAuthException(HTTPException):
    """
    Exception raised when the user is not authorized
    """

    def __init__(self, detail: str) -> None:
        super(InvalidAuthException, self).__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
