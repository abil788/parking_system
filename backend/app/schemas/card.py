from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from ..models.card import CardStatus


class CardBase(BaseModel):
    card_uid: str = Field(..., min_length=1, max_length=100)
    owner_name: str = Field(..., min_length=1, max_length=200)
    vehicle_plate: str = Field(..., min_length=1, max_length=20)
    status: CardStatus = CardStatus.ACTIVE
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    owner_name: Optional[str] = Field(None, min_length=1, max_length=200)
    vehicle_plate: Optional[str] = Field(None, min_length=1, max_length=20)
    status: Optional[CardStatus] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class CardResponse(CardBase):
    id: UUID
    issued_at: datetime

    class Config:
        from_attributes = True


class CardListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    cards: list[CardResponse]