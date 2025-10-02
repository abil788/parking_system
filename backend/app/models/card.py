from sqlalchemy import Column, Integer, String, Boolean
from ..database import Base


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(100), unique=True, nullable=False)  # UID dari kartu RFID
    owner_name = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)  # apakah kartu masih aktif
