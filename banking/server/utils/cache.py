import logging
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Callable, Dict, Generator, List, Optional, Union

from redis.asyncio import Redis as AIORedis
from server.utils.db import BaseModel

from .exceptions import BadRequest, ConfigurationError

_REDIS_HOST = os.environ.get("REDIS_HOST")
_REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
_REDIS_DB = int(os.environ.get("REDIS_DB", 0))
_REDIS_SSL = int(os.environ.get("REDIS_SSL", 0))
_REDIS_CERT_PATH = os.environ.get("REDIS_CERT_PATH")


def construct_resource_lock_key(instance: BaseModel) -> str:
    """This util constructs a lock resource key for a base model instance

    Args:
        instance (BaseModel): Target instance

    Returns:
        str: Lock key
    """
    return f"lock:{instance.__class__.__name__}-{instance.id}"


def read_redis_password() -> Union[str, None]:
    """Reads redis password from file"""
    if _REDIS_CERT_PATH:
        try:
            with open(_REDIS_CERT_PATH, "r") as f:
                return f.read()
        except FileNotFoundError:
            logging.error(f"Couldn't load redis password from path: {_REDIS_CERT_PATH}")
            return None
    return None


_REDIS_PASSWORD = read_redis_password()


def validate_redis_ssl_connection_args():
    if _REDIS_SSL and not _REDIS_CERT_PATH:
        raise ConfigurationError(
            "Redis certificate path must be provided when using SSL mode"
        )


def build_redis_client_connection_args() -> dict:
    """Build redis connection args based on SSL config"""
    connection_args = dict(
        host=_REDIS_HOST, port=_REDIS_PORT, password=_REDIS_PASSWORD, db=_REDIS_DB
    )
    validate_redis_ssl_connection_args()
    if _REDIS_SSL:
        connection_args.update(
            dict(
                ssl=True,
                ssl_cert_reqs="required",
                ssl_ca_certs=_REDIS_CERT_PATH,
            )
        )
    return connection_args


class RedisLock:
    def __init__(self, redis: AIORedis, key: str, lock_timeout: int = 30):
        """
        Initialize the RedisLock.

        Args:
            redis (AIORedis): The async Redis client.
            key (str): The lock key.
            lock_timeout (int): The lock's expiration time in seconds.
        """
        self.redis = redis
        self.key = key
        self.lock_timeout = lock_timeout
        self.lock_value = str(
            datetime.now(datetime.UTC).timestamp()
        )  # Unique value for this lock

    async def acquire(self) -> bool:
        """
        Acquire the lock.

        Returns:
            bool: True if the lock was successfully acquired, False otherwise.
        """
        # Try to set the lock with NX (only set if not exists) and EX (expiration time) options
        is_locked = await self.redis.set(
            self.key, self.lock_value, ex=self.lock_timeout, nx=True
        )
        return is_locked

    async def release(self):
        """
        Release the lock.
        """
        # Only delete the key if it matches the current lock value
        current_value = await self.redis.get(self.key)
        if current_value and current_value.decode() == self.lock_value:
            await self.redis.delete(self.key)

    async def __aenter__(self):
        """
        Context manager entry.
        """
        if not await self.acquire():
            raise BadRequest("Resource is currently locked")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        """
        await self.release()


def get_redis_client(**kwargs) -> AIORedis:
    if kwargs:
        client = AIORedis(**kwargs)
    else:
        client = AIORedis(**build_redis_client_connection_args())
    return client
