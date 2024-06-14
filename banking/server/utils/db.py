from __future__ import annotations

import logging
import os
import ssl
from datetime import datetime
from enum import Enum
from math import ceil
from typing import Any, AsyncGenerator, Dict, List, Optional, Self, Tuple, Type

import pytz
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker as sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import (DeclarativeBase, Mapped, declarative_mixin,
                            declared_attr, mapped_column)

from .exceptions import DBConfigError, DuplicatedEntryError


class ClusterEnvironment(str, Enum):
    """Enumeration for different cluster environments."""

    PRODUCTION = "production"
    TESTING = "testing"
    DEVELOPMENT = "development"
    STAGING = "staging"


_SSL_REQUIRE = os.environ.get("SSL_REQUIRE", False)
_SSL_CERT_PATH = os.environ.get("SSL_CERT_PATH")
_ENVIRONMENT = os.environ.get("ENVIRONMENT", ClusterEnvironment.DEVELOPMENT.value)
_ECHO = _ENVIRONMENT.lower() in {
    ClusterEnvironment.DEVELOPMENT.value,
    ClusterEnvironment.TESTING.value,
}


class DatabaseURLStrategy:
    """Abstract strategy class for constructing database URLs."""

    def construct_db_url(self) -> str:
        """
        Constructs the database URL.

        Returns:
            str: The constructed database URL.
        """
        raise NotImplementedError


class TestDatabaseURLStrategy(DatabaseURLStrategy):
    """Strategy for constructing the database URL for testing environments."""

    def construct_db_url(self) -> str:
        """
        Constructs the database URL for testing environments.

        Raises:
            DBConfigError: If any required environment variable is missing.

        Returns:
            str: The constructed testing database URL.
        """
        try:
            port = os.environ["TEST_DB_PORT"]
            host = os.environ["TEST_DB_HOST"]
            user = os.environ["DB_USER"]
            password = os.environ["DB_PASSWORD"]
            _database = os.environ["DATABASE"]
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{_database}"
        except (AttributeError, KeyError) as e:
            logging.error(f"Requested database keys missing: {e}")
            raise DBConfigError("Improper database config keys") from e


class GeneralDatabaseURLStrategy(DatabaseURLStrategy):
    """Strategy for constructing the database URL for general environments."""

    def construct_db_url(self) -> str:
        """
        Constructs the database URL for general environments.

        Raises:
            DBConfigError: If any required environment variable is missing.

        Returns:
            str: The constructed general database URL.
        """
        try:
            port = os.environ["DB_PORT"]
            host = os.environ["DB_HOST"]
            user = os.environ["DB_USER"]
            password = os.environ["DB_PASSWORD"]
            _database = os.environ["DATABASE"]
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{_database}"
        except (AttributeError, KeyError) as e:
            logging.error(f"Requested database keys missing: {e}")
            raise DBConfigError("Improper database config keys") from e


class DatabaseURLContext:
    """
    Context class for applying the database URL strategy.

    Args:
        strategy (DatabaseURLStrategy): The strategy to use for constructing the URL.
    """

    def __init__(self, strategy: DatabaseURLStrategy):
        self._strategy = strategy

    def construct_url(self) -> str:
        """
        Constructs the database URL using the provided strategy.

        Returns:
            str: The constructed database URL.
        """
        return self._strategy.construct_db_url()


strategy = (
    TestDatabaseURLStrategy()
    if _ENVIRONMENT.lower() == ClusterEnvironment.TESTING.value
    else GeneralDatabaseURLStrategy()
)
db_url_context = DatabaseURLContext(strategy)
url = db_url_context.construct_url()

# SSL context configuration
connect_args = {}
if _SSL_REQUIRE:
    ssl_context = ssl.create_default_context(cafile=_SSL_CERT_PATH)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    connect_args = {"ssl": ssl_context}
    url = f"{url}?ssl={_SSL_REQUIRE}"

# Create the SQLAlchemy engine
engine = create_async_engine(url, echo=_ECHO, connect_args=connect_args)


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all SQLAlchemy models, providing common utilities and attributes.
    Inherits from SQLAlchemy's AsyncAttrs and DeclarativeBase.
    """

    def _asdict(self) -> Dict[str, Any]:
        """
        Converts the SQLAlchemy model instance to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the model.
        """
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Sets the table name for the model based on the class name.

        Returns:
            str: The table name.
        """
        return cls.__name__.lower() + "s"


# Session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_models():
    """
    Initializes database models by creating all tables.

    Usage:
        Call this function during application startup to initialize the database schema.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """
    Dependency function to provide a database session.

    Yields:
        AsyncSession: The SQLAlchemy async session.
    """
    async with async_session() as session:
        yield session


class Page:
    """
    Represents a paginated collection of items.

    Args:
        items (List[Any]): The list of items for the current page.
        page (int): The current page number.
        page_size (int): The number of items per page.
        total (int): The total number of items.
    """

    def __init__(self, items: List[Any], page: int, page_size: int, total: int):
        self.items = items
        self.page = page
        self.page_size = page_size
        self.total = total

    @property
    def pages(self) -> int:
        """
        Calculates the total number of pages.

        Returns:
            int: The total number of pages.
        """
        return ceil(self.total / self.page_size)

    @property
    def has_next(self) -> bool:
        """
        Checks if there is a next page.

        Returns:
            bool: True if a next page exists, otherwise False.
        """
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        """
        Checks if there is a previous page.

        Returns:
            bool: True if a previous page exists, otherwise False.
        """
        return self.page > 1

    @property
    def next_page(self) -> Optional[int]:
        """
        Gets the next page number if it exists.

        Returns:
            Optional[int]: The next page number or None if there is no next page.
        """
        return self.page + 1 if self.has_next else None

    @property
    def prev_page(self) -> Optional[int]:
        """
        Gets the previous page number if it exists.

        Returns:
            Optional[int]: The previous page number or None if there is no previous page.
        """
        return self.page - 1 if self.has_prev else None

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        """
        Iterates over page numbers in the pagination, adding ellipses where necessary.

        Args:
            left_edge (int): Number of pages to show on the left edge.
            left_current (int): Number of pages to show to the left of the current page.
            right_current (int): Number of pages to show to the right of the current page.
            right_edge (int): Number of pages to show on the right edge.

        Yields:
            Optional[int]: Page numbers to display or None for ellipses.
        """
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (
                    num > self.page - left_current - 1
                    and num < self.page + right_current
                )
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


class CRUDMixin(object):
    """
    Mixin providing common CRUD operations for Database models.
    """

    @classmethod
    async def get_by_field(
        cls: Type[Self], value: Any, field: str, session: AsyncSession
    ) -> Self:
        """
        Retrieves a record by a specific field.

        Args:
            cls (Type[Self]): The class type.
            value (Any): The value to search for.
            field (str): The field to search by.
            session (AsyncSession): The database session.

        Returns:
            Self: The retrieved record or None if not found.
        """
        result = await session.execute(select(cls).where(getattr(cls, field) == value))
        return result.scalars().first()

    @classmethod
    async def get_all_by_field(
        cls: Type[Self], value: Any, field: str, session: AsyncSession
    ) -> List[Self]:
        """
        Retrieves all records matching a specific field.

        Args:
            cls (Type[Self]): The class type.
            value (Any): The value to search for.
            field (str): The field to search by.
            session (AsyncSession): The database session.

        Returns:
            List[Self]: A list of matching records.
        """
        result = await session.execute(select(cls).where(getattr(cls, field) == value))
        return result.scalars().all()

    @classmethod
    async def get_by_contains(
        cls: Type[Self], value: Any, field: str, session: AsyncSession
    ) -> Self:
        """
        Retrieves a record where a field contains a specific value.

        Args:
            cls (Type[Self]): The class type.
            value (Any): The value to search for.
            field (str): The field to search by.
            session (AsyncSession): The database session.

        Returns:
            Self: The retrieved record or None if not found.
        """
        result = await session.execute(
            select(cls).where(getattr(cls, field).contains(value))
        )
        return result.scalars().first()

    @classmethod
    async def get_all_by_multiple(
        cls: Type[Self], session: AsyncSession, **kwargs: Any
    ) -> List[Self]:
        """
        Retrieves all records matching multiple fields.

        Args:
            cls (Type[Self]): The class type.
            session (AsyncSession): The database session.
            **kwargs (Any): Key-value pairs of fields and values to match.

        Returns:
            List[Self]: A list of matching records.
        """
        result = await session.execute(select(cls).filter_by(**kwargs))
        return result.scalars().all()

    @classmethod
    async def get_one_by_multiple(
        cls: Type[Self], session: AsyncSession, **kwargs: Any
    ) -> Self:
        """
        Retrieves a single record matching multiple fields.

        Args:
            cls (Type[Self]): The class type.
            session (AsyncSession): The database session.
            **kwargs (Any): Key-value pairs of fields and values to match.

        Returns:
            Self: The retrieved record or None if not found.
        """
        result = await session.execute(select(cls).filter_by(**kwargs))
        return result.scalars().first()

    @classmethod
    async def get_all(cls: Type[Self], session: AsyncSession) -> List[Self]:
        """
        Retrieves all records of the model.

        Args:
            cls (Type[Self]): The class type.
            session (AsyncSession): The database session.

        Returns:
            List[Self]: A list of all records.
        """
        result = await session.execute(select(cls).order_by(cls.created_at.desc()))
        return result.scalars().all()

    @classmethod
    async def total_count(cls: Type[Self], session: AsyncSession) -> int:
        """
        Counts the total number of records of the model.

        Args:
            cls (Type[Self]): The class type.
            session (AsyncSession): The database session.

        Returns:
            int: The total number of records.
        """
        result = await session.execute(select(func.count(cls.id)))
        return result.scalar()

    @classmethod
    async def paginate(
        cls: Type[Self],
        page: int,
        session: AsyncSession,
        page_size: int = 20,
        **query: Any,
    ) -> Page:
        """
        Paginates the records of the model.

        Args:
            cls (Type[Self]): The class type.
            page (int): The current page number.
            session (AsyncSession): The database session.
            page_size (int, optional): The number of items per page. Defaults to 20.
            **query (Any): Additional query filters.

        Returns:
            Page: The paginated records.
        """
        if page <= 0:
            raise AttributeError("page needs to be >= 1")
        if page_size <= 0:
            raise AttributeError("page_size needs to be >= 1")

        query_stmt = select(cls).filter_by(**query) if query else select(cls)
        query_stmt = query_stmt.limit(page_size).offset((page - 1) * page_size)

        result = await session.execute(query_stmt)
        items = result.scalars().all()
        total = await cls.total_count(session)
        return Page(items, page, page_size, total)

    @classmethod
    async def find_latest(cls: Type[Self], session: AsyncSession) -> List[Self]:
        """
        Finds the latest records based on the `updated_at` timestamp.

        Args:
            cls (Type[Self]): The class type.
            session (AsyncSession): The database session.

        Returns:
            List[Self]: A list of the latest records.
        """
        result = await session.execute(select(cls).order_by(cls.updated_at.desc()))
        return result.scalars().all()

    async def update(
        self, session: AsyncSession, commit: bool = True, **kwargs: Any
    ) -> Self:
        """
        Updates specific fields of the record.

        Args:
            session (AsyncSession): The database session.
            commit (bool, optional): Whether to commit the transaction. Defaults to True.
            **kwargs (Any): The fields to update.

        Returns:
            Self: The updated record.
        """
        kwargs.pop("id", None)  # Prevent changing the ID
        kwargs["updated_at"] = datetime.now()  # Update the timestamp

        for attr, value in kwargs.items():
            if value is not None:
                setattr(self, attr, value)

        return await self.save(session, commit=commit)

    @classmethod
    async def create(cls: Type[Self], session: AsyncSession, **kwargs: Any) -> Self:
        """
        Creates a new record and saves it to the database.

        Args:
            cls (Type[Self]): The class type.
            session (AsyncSession): The database session.
            **kwargs (Any): The fields for the new record.

        Returns:
            Self: The created record.
        """
        instance = cls(**kwargs)
        return await instance.save(session=session)

    async def save(self, session: AsyncSession, commit: bool = True) -> Self:
        """
        Saves the record.

        Args:
            session (AsyncSession): The database session.
            commit (bool, optional): Whether to commit the transaction. Defaults to True.

        Returns:
            Self: The saved record.
        """
        session.add(self)
        if commit:
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise DuplicatedEntryError(
                    f"The {self.__class__.__name__} instance already exists"
                )
        return self

    async def delete(self, session: AsyncSession) -> None:
        """
        Deletes the record from the database.

        Args:
            session (AsyncSession): The database session.
        """
        await session.delete(self)
        await session.commit()

    """ Utility functions """

    @classmethod
    def date_to_string(cls, raw_date: datetime) -> str:
        """
        Converts a datetime object to a string representation.

        Args:
            raw_date (datetime): The datetime object.

        Returns:
            str: The string representation of the date.
        """
        return raw_date.isoformat()


@declarative_mixin
class BaseModel(CRUDMixin, Base):
    """
    Base model class that includes CRUD convenience methods.
    """

    __abstract__ = True
    __table_args__ = {"extend_existing": True}
    __mapper_args__ = {"always_refresh": True}

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now(), onupdate=datetime.now()
    )


def split_name(full_name: str) -> Tuple[str, str]:
    """
    Splits a full name into first and last name.

    Args:
        full_name (str): The full name to split.

    Returns:
        Tuple[str, str]: The first and last name.
    """
    name_parts = full_name.split()
    if len(name_parts) < 2:
        return full_name, ""  # Handle case where there is no last name
    return name_parts[0], " ".join(name_parts[1:])
