import logging
from datetime import datetime, timedelta

from httpx import AsyncClient
from jwt.jwks_client import PyJWKClient

logger = logging.getLogger(__name__)


class OpenIdConfig:
    def __init__(
        self,
        config_url: str,
        timeout_in_h: int,
    ) -> None:
        self.config_url = config_url
        self.timeout_in_h = timeout_in_h

        self._config_timestamp: datetime | None = None

        self.authorization_endpoint: str
        self.token_endpoint: str
        self.issuer: str
        self.jwks_client: PyJWKClient

    async def load_config(self) -> None:
        """
        Loads config from the openid-config endpoint if it's not cached or it's over 24 hours old
        """
        refresh_time = datetime.now() - timedelta(hours=self.timeout_in_h)
        if not self._config_timestamp or self._config_timestamp < refresh_time:
            try:
                logger.info("Loading OpenID configuration.")
                await self._load_openid_config()
                self._config_timestamp = datetime.now()
            except Exception as error:
                logger.error("Unable to load OpenID configuration", exc_info=True)
                raise RuntimeError("Unable to load OpenID configuration.") from error

            logger.info(
                (
                    "Successfully loaded OpenID configuration:\n"
                    "authorization endpoint: %s\n"
                    "token endpoint: %s\n"
                    "issuer: %s"
                ),
                self.authorization_endpoint,
                self.token_endpoint,
                self.issuer,
            )

    async def _load_openid_config(self) -> None:
        """
        Load openid config, fetch signing keys
        """
        async with AsyncClient(timeout=10) as client:
            logger.info("Fetching OpenID Connect config from %s", self.config_url)
            openid_response = await client.get(self.config_url)
            openid_response.raise_for_status()
            openid_cfg = openid_response.json()

            self.authorization_endpoint = openid_cfg["authorization_endpoint"]
            self.token_endpoint = openid_cfg["token_endpoint"]
            self.issuer = openid_cfg["issuer"]

            jwks_uri = openid_cfg["jwks_uri"]
            self.jwks_client = PyJWKClient(jwks_uri, cache_keys=True)
