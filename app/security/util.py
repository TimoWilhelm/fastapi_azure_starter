from typing import Optional


def get_azure_config_url(tenant_id: Optional[str]) -> str:
    tenant_id = tenant_id or "common"
    return f'https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration'
