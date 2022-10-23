from typing import Dict, List, Optional

from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from fastapi.security.base import SecurityBase
from fastapi.openapi.models import SecurityBase as SecurityBaseModel

from starlette.requests import Request

from jwt import decode as jwt_decode
from jwt.exceptions import PyJWKClientError, DecodeError

from .exceptions import InvalidAuth
from .openid_config import OpenIdConfig
from .user import User

from app.logging import get_logger

logger = get_logger(__name__)


class AzureAuthorizationCodeBearerBase(SecurityBase):
    def __init__(
        self,
        client_id: str,
        tenant_id: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        multi_tenant: bool = False,
        algorithms: List[str] = ["RS256"],
        auto_error: bool = True,
        openapi_description: Optional[str] = None,
    ) -> None:
        """
        Initialize settings.
        :param client_id: str
            Your application client ID.
        :param auto_error: bool
            Whether to throw exceptions or return None on __call__.
        :param tenant_id: str
            Your Azure tenant ID, only needed for single tenant apps
        :param scopes: Optional[dict[str, str]
            Scopes, these are the ones you've configured in Azure AD.
            Key is scope, value is a description.
            Example:
                {
                    f'api://{settings.CLIENT_ID}/user_impersonation': 'user impersonation'
                }
        :param multi_tenant: bool
            Whether this is a multi tenant or single tenant application.
        :param algorithms: List[str]
            The supported signing key algorithms for the token.
        :param openapi_description: str
            Override OpenAPI description
        """
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.scopes = scopes
        self.multi_tenant = multi_tenant
        self.algorithms = algorithms
        self.auto_error = auto_error
        self.openapi_description = openapi_description

        self.openid_config: OpenIdConfig = OpenIdConfig(
            tenant_id=tenant_id,
            multi_tenant=self.multi_tenant,
        )

        self.oauth: OAuth2AuthorizationCodeBearer
        self.model: SecurityBaseModel

    def _verify(self, token: str):
        try:
            jwk = self.signing_key = self.openid_config.jwks_client.get_signing_key_from_jwt(
                token
            )
        except PyJWKClientError as e:
            raise InvalidAuth(e.__str__())

        try:
            payload = jwt_decode(
                jwt=token,
                key=jwk.key,
                verify=True,
                algorithms=self.algorithms,
                audience=self.client_id,
                issuer=self.openid_config.issuer,
            )
        except DecodeError as e:
            raise InvalidAuth(e.__str__())

        return payload

    async def init(self):
        await self.openid_config.load_config()

        self.oauth = OAuth2AuthorizationCodeBearer(
            authorizationUrl=self.openid_config.authorization_endpoint,
            tokenUrl=self.openid_config.token_endpoint,
            scopes=self.scopes,
            scheme_name='AzureAuthorizationCodeBearerBase',
            description=self.openapi_description,
            auto_error=True,  # We catch this exception in __call__
        )
        self.model = self.oauth.model

    async def __call__(self, request: Request, security_scopes: SecurityScopes) -> Optional[User]:
        """
        Extends call validate the token.
        """

        # refresh config
        await self.openid_config.load_config()

        try:
            access_token = await self.oauth(request=request)

            if (access_token is None):
                raise InvalidAuth('No access token provided')

            claims = self._verify(access_token)

            token_scope_string = claims.get('scp', '')
            if not isinstance(token_scope_string, str):
                raise InvalidAuth('Token contains invalid formatted scopes')
            token_scopes = token_scope_string.split(' ')
            for scope in security_scopes.scopes:
                if scope not in token_scopes:
                    raise InvalidAuth('Required scope missing')

            # Attach the user to the request. Can be accessed through `request.state.user`
            user: User = User(**{**claims, 'claims': claims, 'access_token': access_token})
            request.state.user = user
            return user

        except (HTTPException, InvalidAuth):
            if not self.auto_error:
                return None
            raise


class SingleTenantAzureAuthorizationCodeBearer(AzureAuthorizationCodeBearerBase):
    def __init__(
        self,
        client_id: str,
        tenant_id: str,
        scopes: Optional[Dict[str, str]] = None,
        algorithms: List[str] = ["RS256"],
        auto_error: bool = True,
        openapi_description: Optional[str] = None,
    ) -> None:
        """
        Initialize settings for a single tenant application.
        :param client_id: str
            Your application client ID.
        :param tenant_id: str
            Your Azure tenant ID
        :param scopes: Optional[dict[str, str]
            Scopes, these are the ones you've configured in Azure AD.
            Key is scope, value is a description.
            Example:
                {
                    f'api://{settings.CLIENT_ID}/user_impersonation': 'user impersonation'
                }
        :param algorithms: List[str]
            The supported signing key algorithms for the token.
        :param auto_error: bool
            Whether to throw exceptions or return None on __call__.
        :param openapi_description: str
            Override OpenAPI description
        """
        super().__init__(
            client_id=client_id,
            tenant_id=tenant_id,
            scopes=scopes,
            algorithms=algorithms,
            auto_error=auto_error,
            openapi_description=openapi_description,
        )
        self.scheme_name: str = 'Azure AD - PKCE, Single-tenant'


class MultiTenantAzureAuthorizationCodeBearer(AzureAuthorizationCodeBearerBase):
    def __init__(
        self,
        client_id: str,
        scopes: Optional[Dict[str, str]] = None,
        algorithms: List[str] = ["RS256"],
        auto_error: bool = True,
        openapi_description: Optional[str] = None,
    ) -> None:
        """
        Initialize settings for a multi-tenant application.
        :param client_id: str
            Your application client ID.
        :param scopes: Optional[dict[str, str]
            Scopes, these are the ones you've configured in Azure AD.
            Key is scope, value is a description.
            Example:
                {
                    f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'user impersonation'
                }
        :param algorithms: List[str]
            The supported signing key algorithms for the token.
        :param auto_error: bool
            Whether to throw exceptions or return None on __call__.
        :param openapi_description: str
            Override OpenAPI description
        """
        super().__init__(
            client_id=client_id,
            scopes=scopes,
            multi_tenant=True,
            algorithms=algorithms,
            auto_error=auto_error,
            openapi_description=openapi_description,
        )
        self.scheme_name: str = 'Azure AD - PKCE, Multi-tenant'
