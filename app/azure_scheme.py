from app.packages.auth import OidcAuthorizationCodeBearer
from app.packages.auth.util import get_azure_oidc_config_url


class AzureScheme:
    _scheme: OidcAuthorizationCodeBearer | None = None

    @classmethod
    def init(cls, tenant_id: str, client_id: str):
        cls._scheme = OidcAuthorizationCodeBearer(
            name="Azure AD",
            config_url=get_azure_oidc_config_url(tenant_id),
            client_id=client_id,
            scopes={
                f"api://{client_id}/user_impersonation": "user_impersonation",
            },
        )

    @classmethod
    def instance(cls):
        if cls._scheme is None:  # pragma: no cover
            raise RuntimeError("AzureScheme not initialized")
        return cls._scheme
