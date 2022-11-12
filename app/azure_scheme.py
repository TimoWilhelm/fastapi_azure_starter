from app.packages.auth import OidcAuthorizationCodeBearer
from app.packages.auth.util import get_azure_oidc_config_url


def get_azure_scheme(tenant_id: str, client_id: str):
    return OidcAuthorizationCodeBearer(
        name="Azure AD",
        config_url=get_azure_oidc_config_url(tenant_id),
        client_id=client_id,
        scopes={
            f"api://{client_id}/user_impersonation": "user_impersonation",
        },
    )
