from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL, echo=True)

# SessionLocal = database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model untuk inheritance
Base = declarative_base()


# Dependency untuk FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
