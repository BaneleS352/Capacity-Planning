import re
from collections.abc import AsyncIterator

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


def database_url(settings: Settings) -> str | URL:
    if not settings.database_connection_string:
        return settings.database_url

    connection_string = settings.database_connection_string.strip().rstrip(";")
    # ADO.NET calls this option MultipleActiveResultSets; the ODBC equivalent is MARS_Connection.
    connection_string = connection_string.replace(
        "MultipleActiveResultSets=", "MARS_Connection="
    ).replace("multipleactiveresultsets=", "MARS_Connection=")
    connection_string = re.sub(
        r"(?i)\b(Trusted_Connection|MARS_Connection)\s*=\s*true\b",
        r"\1=Yes",
        connection_string,
    )
    connection_string = re.sub(
        r"(?i)\b(Trusted_Connection|MARS_Connection)\s*=\s*false\b",
        r"\1=No",
        connection_string,
    )
    # C# literals commonly contain a doubled slash before a named SQL Server instance.
    connection_string = connection_string.replace("\\\\", "\\")
    if "driver=" not in connection_string.casefold():
        connection_string = f"DRIVER={{{settings.database_odbc_driver}}};{connection_string}"
    is_localdb = "(localdb)" in connection_string.casefold()
    trusts_server_certificate = "trustservercertificate=" in connection_string.casefold()
    if is_localdb and not trusts_server_certificate:
        connection_string = f"{connection_string};TrustServerCertificate=Yes"

    return URL.create("mssql+aioodbc", query={"odbc_connect": connection_string})


def create_engine(settings: Settings) -> AsyncEngine:
    url = database_url(settings)
    kwargs: dict[str, object] = {
        "echo": settings.database_echo,
        "pool_pre_ping": True,
    }
    if not str(url).startswith("sqlite"):
        kwargs.update(pool_size=10, max_overflow=20, pool_recycle=1800)
    return create_async_engine(url, **kwargs)


settings = get_settings()
engine = create_engine(settings)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
