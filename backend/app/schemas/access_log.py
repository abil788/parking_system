from pydantic import BaseModel
from datetime import datetime


class AccessLogBase(BaseModel):
    card_id: int
    reader_id: int
    status: str


class AccessLogCreate(AccessLogBase):
    pass


class AccessLogResponse(AccessLogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
