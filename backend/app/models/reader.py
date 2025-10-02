from sqlalchemy import Column, Integer, String
from ..database import Base


class Reader(Base):
    __tablename__ = "readers"

    id = Column(Integer, primary_key=True, index=True)
    reader_id = Column(String(100), unique=True, nullable=False)  # UUID dari device
    location = Column(String(100), nullable=True)  # lokasi reader, ex: "Gate A"
