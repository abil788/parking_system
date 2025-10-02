from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.ReaderResponse)
def create_reader(reader: schemas.ReaderCreate, db: Session = Depends(get_db)):
    db_reader = models.Reader(**reader.dict())
    db.add(db_reader)
    db.commit()
    db.refresh(db_reader)
    return db_reader


@router.get("/", response_model=list[schemas.ReaderResponse])
def list_readers(db: Session = Depends(get_db)):
    return db.query(models.Reader).all()
