from sqlalchemy.engine import URL

from app.core.config import Settings
from app.infrastructure.database.session import database_url


def test_adonet_connection_string_is_converted_for_async_odbc() -> None:
    settings = Settings(
        database_connection_string=(
            r"Server=(localdb)\\MSSQLLocalDB;Database=betteams;"
            "Trusted_Connection=True;MultipleActiveResultSets=true"
        )
    )

    url = database_url(settings)

    assert isinstance(url, URL)
    assert url.drivername == "mssql+aioodbc"
    assert url.query["odbc_connect"] == (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        r"Server=(localdb)\MSSQLLocalDB;Database=betteams;"
        "Trusted_Connection=Yes;MARS_Connection=Yes;TrustServerCertificate=Yes"
    )


def test_database_url_remains_available_for_sqlite_and_postgres() -> None:
    settings = Settings(
        database_url="sqlite+aiosqlite:///test.db", database_connection_string=None
    )

    assert database_url(settings) == "sqlite+aiosqlite:///test.db"
