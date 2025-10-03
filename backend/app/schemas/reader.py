from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from ..models.reader import ReaderType, ReaderStatus


class ReaderBase(BaseModel):
    location: str = Field(..., min_length=1, max_length=200)
    type: ReaderType
    status: ReaderStatus = ReaderStatus.ACTIVE


class ReaderCreate(ReaderBase):
    pass


class ReaderUpdate(BaseModel):
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[ReaderType] = None
    status: Optional[ReaderStatus] = None


class ReaderResponse(ReaderBase):
    id: UUID

    class Config:
        from_attributes = True


class ReaderEventRequest(BaseModel):
    card_uid: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., pattern="^(enter|exit)$")


class ReaderEventResponse(BaseModel):
    result: str  # granted or denied
    reason: Optional[str] = None
    message: str
    owner_name: Optional[str] = None
    vehicle_plate: Optional[str] = None