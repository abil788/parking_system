from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .config import settings

# Create all tables jika belum ada
Base.metadata.create_all(bind=engine)

# Init FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)


@app.get("/")
def root():
    return {"message": "Parking System API is running 🚗"}


@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")  # cek koneksi
        return {"database": "connected"}
    except Exception as e:
        return {"database": f"error - {e}"}
