from datetime import timedelta
from typing import List, Optional

from fastapi_jwt import JwtAccessBearer
from pydantic import EmailStr
from server.config.settings import get_settings
from server.models.user import User, UserRole, UserToken
from server.schemas.accounts import UserAccountSchema
from server.utils.exceptions import (BadRequest, DuplicatedEntryError,
                                     ObjectNotFound)
from sqlalchemy.ext.asyncio import AsyncSession

_USER_NOT_FOUND_ERROR_MESSAGE = "User doesn't exist"
