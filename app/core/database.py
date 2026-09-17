from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_consult_status_enum() -> None:
    """Add new ConsultStatus values to an existing Postgres enum (create_all will not)."""
    from sqlalchemy.exc import ProgrammingError

    from app.models.consult import ConsultStatus

    try:
        with engine.begin() as connection:
            for member in ConsultStatus:
                connection.execute(
                    text(
                        f"ALTER TYPE consult_status ADD VALUE IF NOT EXISTS '{member.value}'"
                    )
                )
    except ProgrammingError:
        # Type not created yet; create_all on API startup will define it.
        pass
