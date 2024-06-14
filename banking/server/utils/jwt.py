from fastapi_jwt import JwtAccessBearer, JwtAuthorizationCredentials
from server.config.settings import settings

access_security = JwtAccessBearer(secret_key=settings.SECRET_KEY, auto_error=True)
