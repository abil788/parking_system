from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from ..models.access_log import AccessAction, AccessResult


class AccessLogResponse(BaseModel):
    id: UUID
    card_id: Optional[UUID]
    reader_id: UUID
    timestamp: datetime
    action: AccessAction
    result: AccessResult
    reason: Optional[str]
    
    # Extra fields from relationships
    card_uid: Optional[str] = None
    owner_name: Optional[str] = None
    vehicle_plate: Optional[str] = None
    reader_location: Optional[str] = None
    reader_type: Optional[str] = None

    class Config:
        from_attributes = True


class AccessLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    logs: list[AccessLogResponse]