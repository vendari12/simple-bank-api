from fastapi_jwt import JwtAccessBearer, JwtAuthorizationCredentials
from server.config.settings import get_settings

access_security = JwtAccessBearer(secret_key=get_settings().SECRET_KEY, auto_error=True)
