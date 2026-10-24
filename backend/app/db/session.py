from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Serverless instances are frozen between requests, so a client-side pool would hold
# dead connections; open one per request and let the provider's pooler do the pooling.
engine_kwargs = {"poolclass": NullPool} if settings.VERCEL else {"pool_pre_ping": True}
engine = create_engine(settings.DATABASE_URL, future=True, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
