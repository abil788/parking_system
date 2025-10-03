import uuid
from sqlalchemy import Column, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum
from ..database import Base


class CardStatus(str, enum.Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    LOST = "lost"


class Card(Base):
    __tablename__ = "cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_uid = Column(String(100), unique=True, nullable=False, index=True)
    owner_name = Column(String(200), nullable=False)
    vehicle_plate = Column(String(20), nullable=False)
    status = Column(Enum(CardStatus), default=CardStatus.ACTIVE, nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    def is_valid(self) -> bool:
        """Check if card is valid for access"""
        if self.status != CardStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def get_denial_reason(self) -> str:
        """Get reason why card is denied"""
        if self.status == CardStatus.BLOCKED:
            return "blocked"
        elif self.status == CardStatus.LOST:
            return "lost"
        elif self.expires_at and self.expires_at < datetime.utcnow():
            return "expired"
        return "invalid"