def get_azure_oidc_config_url(tenant_id: str = "common") -> str:
    return f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration"
