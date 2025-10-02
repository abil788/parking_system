from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.AccessLogResponse)
def create_log(log: schemas.AccessLogCreate, db: Session = Depends(get_db)):
    db_log = models.AccessLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


@router.get("/", response_model=list[schemas.AccessLogResponse])
def list_logs(db: Session = Depends(get_db)):
    return db.query(models.AccessLog).all()
