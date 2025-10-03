import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database import Base


class AccessAction(str, enum.Enum):
    ENTER = "enter"
    EXIT = "exit"


class AccessResult(str, enum.Enum):
    GRANTED = "granted"
    DENIED = "denied"


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id", ondelete="CASCADE"), nullable=True)
    reader_id = Column(UUID(as_uuid=True), ForeignKey("readers.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    action = Column(Enum(AccessAction), nullable=False)
    result = Column(Enum(AccessResult), nullable=False)
    reason = Column(String(100), nullable=True)
    
    # Relationships
    card = relationship("Card", backref="access_logs")
    reader = relationship("Reader", backref="access_logs")