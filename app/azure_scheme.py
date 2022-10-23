
from .security import SingleTenantAzureAuthorizationCodeBearer

from app import settings

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes={
        f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'user_impersonation',
    }
)
