"""Engine and session factory. Nothing connects until a session is first used."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import settings

engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle_s,
    pool_pre_ping=True,  # drop dead connections (e.g. after a managed-DB failover)
    echo=settings.db_echo,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: `def endpoint(db: Session = Depends(get_db))`."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
