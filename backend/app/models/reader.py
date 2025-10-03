import uuid
from sqlalchemy import Column, String, Enum
from sqlalchemy.dialects.postgresql import UUID
import enum
from ..database import Base


class ReaderType(str, enum.Enum):
    ENTRY = "entry"
    EXIT = "exit"


class ReaderStatus(str, enum.Enum):
    ACTIVE = "active"
    OFFLINE = "offline"


class Reader(Base):
    __tablename__ = "readers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location = Column(String(200), nullable=False)
    type = Column(Enum(ReaderType), nullable=False)
    status = Column(Enum(ReaderStatus), default=ReaderStatus.ACTIVE, nullable=False)