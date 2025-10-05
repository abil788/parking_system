from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Increase connection pool
    max_overflow=40,           # Allow 40 more connections if needed
    pool_pre_ping=True,        # Check connection health
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=settings.DEBUG,
    connect_args={
        "connect_timeout": 10,
        "options": "-c timezone=utc"
    }
)

# Enable query optimization
@event.listens_for(engine, "connect")
def set_postgres_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET work_mem = '16MB'")
    cursor.execute("SET maintenance_work_mem = '64MB'")
    cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Don't expire objects after commit
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()