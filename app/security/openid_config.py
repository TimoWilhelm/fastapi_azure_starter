from datetime import datetime, timedelta

from typing import Optional

from fastapi import HTTPException, status

from httpx import AsyncClient

from jwt.jwks_client import PyJWKClient

from app.logging import get_logger

logger = get_logger(__name__)


class OpenIdConfig:
    def __init__(
        self,
        tenant_id: Optional[str] = None,
        multi_tenant: bool = False,
    ) -> None:
        self.tenant_id: Optional[str] = tenant_id
        self._config_timestamp: Optional[datetime] = None
        self.multi_tenant: bool = multi_tenant

        self.authorization_endpoint: str
        self.token_endpoint: str
        self.issuer: str
        self.jwks_client: PyJWKClient

    async def load_config(self) -> None:
        """
        Loads config from the openid-config endpoint if it's not cached or it's over 24 hours old
        """
        refresh_time = datetime.now() - timedelta(hours=24)
        if not self._config_timestamp or self._config_timestamp < refresh_time:
            try:
                logger.debug('Loading Azure AD OpenID configuration.')
                await self._load_openid_config()
                self._config_timestamp = datetime.now()
            except Exception as error:
                logger.exception(
                    'Unable to fetch OpenID configuration from Azure AD. Error: %s', error)
                # We can't fetch an up to date openid-config, so authentication will not work.
                if self._config_timestamp:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='Unable to fetch Azure AD configuration',
                        headers={'WWW-Authenticate': 'Bearer'},
                    ) from error

                else:
                    raise RuntimeError(f'Unable to fetch provider information. {error}') from error

            logger.info((
                "Successfully fetched OpenID configuration from Azure AD:\n"
                "authorization endpoint: %s\n"
                "token endpoint: %s\n"
                "issuer: %s"
            ), self.authorization_endpoint, self.token_endpoint, self.issuer)

    async def _load_openid_config(self) -> None:
        """
        Load openid config, fetch signing keys
        """
        path = 'common' if self.multi_tenant else self.tenant_id
        config_url = f'https://login.microsoftonline.com/{path}/v2.0/.well-known/openid-configuration'  # noqa: E501

        async with AsyncClient(timeout=10) as client:
            logger.info('Fetching OpenID Connect config from %s', config_url)
            openid_response = await client.get(config_url)
            openid_response.raise_for_status()
            openid_cfg = openid_response.json()

            self.authorization_endpoint = openid_cfg['authorization_endpoint']
            self.token_endpoint = openid_cfg['token_endpoint']
            self.issuer = openid_cfg['issuer']

            jwks_uri = openid_cfg['jwks_uri']
            self.jwks_client = PyJWKClient(jwks_uri)
