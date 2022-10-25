from app.packages.security import OidcAuthorizationCodeBearer
from app.packages.security.util import get_azure_oidc_config_url

from app import settings


azure_scheme = OidcAuthorizationCodeBearer(
    config_url=get_azure_oidc_config_url(settings.TENANT_ID),
    client_id=settings.APP_CLIENT_ID,
    scopes={
        f"api://{settings.APP_CLIENT_ID}/user_impersonation": "user_impersonation",
    },
)
