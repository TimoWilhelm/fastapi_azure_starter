import logging

from fastapi.exceptions import HTTPException
from fastapi.security import (
    OAuth2AuthorizationCodeBearer as FastApiOAuth2AuthorizationCodeBearer,
)
from fastapi.security import SecurityScopes
from fastapi.security.base import SecurityBase
from jwt import decode as jwt_decode
from jwt.exceptions import InvalidTokenError, PyJWTError
from starlette.requests import Request

from .exceptions import InvalidAuthException, NotInitializedException
from .openid_config import OpenIdConfig
from .user import User

logger = logging.getLogger(__name__)


class OidcAuthorizationCodeBearer(SecurityBase):
    _oauth: FastApiOAuth2AuthorizationCodeBearer | None = None

    def __init__(
        self,
        config_url: str,
        client_id: str,
        scopes: dict[str, str] | None = None,
        algorithms: list[str] | None = None,
        auto_error: bool = True,
        config_timeout_in_h: int = 24,
        name: str = "OpenID Connect",
        openapi_description: str | None = None,
    ) -> None:
        """Returns a security scheme that uses OpenID Connect to authenticate users.

        Args:
            config_url (str):
                The OpenID Connect Discovery URL.
            client_id (str):
                The API client ID.
            scopes (dict[str, str], optional):
                The OAuth Scopes your application uses.
                Defaults to None.

                The Key is the scope, value is a description.
                Example:
                    {
                        f'api://example.com/user_impersonation': 'user impersonation'
                    }
            algorithms (list[str], optional):
                The supported signing key algorithms for the token.
                Defaults to ["RS256", "RS384", "RS512"].
            auto_error (bool, optional):
                Whether to throw exceptions or return None on __call__. Defaults to True.
            config_timeout_in_h (int, optional):
                The number of hours to cache the OpenID Connect Discovery document. Defaults to 24.
            name (str, optional):
                The OpenAPI name of the auth scheme. Defaults to "OpenID Connect".
            openapi_description (str, optional):
                The OpenAPI description of the auth scheme. Defaults to None.
        """
        self.client_id = client_id
        self.scopes = scopes
        self.algorithms = algorithms or ["RS256", "RS384", "RS512"]
        self.auto_error = auto_error
        self.scheme_name = name
        self.openapi_description = openapi_description

        self.openid_config: OpenIdConfig = OpenIdConfig(
            config_url=config_url, timeout_in_h=config_timeout_in_h
        )

    @property
    def oauth(self):
        if not self._oauth:
            raise NotInitializedException()
        return self._oauth

    @property
    def model(self):
        return self.oauth.model

    def _verify(self, token: str):
        try:
            jwk = (
                self.signing_key
            ) = self.openid_config.jwks_client.get_signing_key_from_jwt(token)

            payload = jwt_decode(
                jwt=token,
                key=jwk.key,
                algorithms=self.algorithms,
                audience=self.client_id,
                issuer=self.openid_config.issuer,
            )
        except InvalidTokenError as e:
            logger.warning("Invalid token", exc_info=True)
            raise InvalidAuthException("Invalid token") from e
        except PyJWTError as e:
            logger.error("Token validation failed", exc_info=True)
            raise InvalidAuthException("Token validation failed") from e

        return payload

    async def init(self):
        await self.openid_config.load_config()

        self._oauth = FastApiOAuth2AuthorizationCodeBearer(
            authorizationUrl=self.openid_config.authorization_endpoint,
            tokenUrl=self.openid_config.token_endpoint,
            scopes=self.scopes,
            description=self.openapi_description,
            auto_error=True,  # We catch this exception in __call__
        )

    async def __call__(
        self, request: Request, security_scopes: SecurityScopes
    ) -> User | None:
        # refresh config if needed
        await self.openid_config.load_config()

        try:
            access_token = await self.oauth(request=request)

            if access_token is None:
                raise InvalidAuthException("No access token provided")

            claims = self._verify(access_token)

            token_scope_string: str = claims.get("scp", "")

            if not isinstance(token_scope_string, str):
                raise InvalidAuthException("Token contains invalid formatted scopes")

            token_scopes = token_scope_string.split(" ")

            for scope in security_scopes.scopes:
                if scope not in token_scopes:
                    raise InvalidAuthException("Required scope missing")

            # Attach the user to the request. Can be accessed through `request.state.user`
            user: User = User(
                **{**claims, "claims": claims, "access_token": access_token}
            )
            request.state.user = user
            return user

        except (HTTPException, InvalidAuthException):
            if not self.auto_error:
                return None
            raise
