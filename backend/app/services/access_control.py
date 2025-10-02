from sqlalchemy.orm import Session
from datetime import datetime
from typing import Tuple, Optional
from app.models.card import Card, CardStatus
from app.models.reader import Reader, ReaderType
from app.models.access_log import AccessLog, AccessType, AccessStatus
from app.config import settings


class AccessControlService:
    """Service for handling access control logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_card_access(self, card_uid: str, reader_id: int) -> Tuple[bool, str, Optional[Card]]:
        """
        Validate if a card can access through a reader
        Returns: (is_valid, message, card)
        """
        # Get card
        card = self.db.query(Card).filter(Card.card_uid == card_uid).first()
        if not card:
            return False, "Card not found", None
        
        # Check card status
        if card.status != CardStatus.ACTIVE:
            return False, f"Card is {card.status.value}", card
        
        # Check expiry
        if card.valid_until and card.valid_until < datetime.utcnow():
            card.status = CardStatus.EXPIRED
            self.db.commit()
            return False, "Card has expired", card
        
        # Get reader
        reader = self.db.query(Reader).filter(Reader.id == reader_id).first()
        if not reader or not reader.is_active:
            return False, "Reader is not active", card
        
        return True, "Access granted", card
    
    def log_access(
        self,
        card_id: int,
        reader_id: int,
        access_type: AccessType,
        access_status: AccessStatus,
        notes: Optional[str] = None
    ) -> AccessLog:
        """Create an access log entry"""
        access_log = AccessLog(
            card_id=card_id,
            reader_id=reader_id,
            access_type=access_type,
            access_status=access_status,
            notes=notes
        )
        
        self.db.add(access_log)
        
        # Update reader last read time
        reader = self.db.query(Reader).filter(Reader.id == reader_id).first()
        if reader:
            reader.last_read_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(access_log)
        
        return access_log
    
    def calculate_parking_fee(self, entry_time: datetime, exit_time: datetime) -> Tuple[int, float]:
        """
        Calculate parking duration and fee
        Returns: (duration_minutes, fee)
        """
        duration = exit_time - entry_time
        duration_minutes = int(duration.total_seconds() / 60)
        duration_hours = duration_minutes / 60
        
        # Calculate fee (rounded up to nearest hour)
        import math
        hours_to_charge = math.ceil(duration_hours)
        fee = hours_to_charge * settings.PARKING_RATE_PER_HOUR
        
        return duration_minutes, fee
    
    def process_card_read(self, card_uid: str, reader_id: int) -> dict:
        """
        Process a card read event
        Returns: dictionary with access result
        """
        # Validate access
        is_valid, message, card = self.validate_card_access(card_uid, reader_id)
        
        # Get reader info
        reader = self.db.query(Reader).filter(Reader.id == reader_id).first()
        
        if not is_valid or not card:
            # Log denied access
            if card:
                self.log_access(
                    card.id,
                    reader_id,
                    AccessType.ENTRY if reader.reader_type == ReaderType.ENTRY else AccessType.EXIT,
                    AccessStatus.DENIED,
                    message
                )
            
            return {
                "access_granted": False,
                "message": message,
                "card_uid": card_uid
            }
        
        # Determine access type based on reader type
        access_type = AccessType.ENTRY if reader.reader_type == ReaderType.ENTRY else AccessType.EXIT
        
        # For exit, calculate parking fee
        parking_duration = None
        parking_fee = None
        
        if access_type == AccessType.EXIT:
            # Find the last entry log for this card
            last_entry = self.db.query(AccessLog).filter(
                AccessLog.card_id == card.id,
                AccessLog.access_type == AccessType.ENTRY,
                AccessLog.access_status == AccessStatus.GRANTED
            ).order_by(AccessLog.access_time.desc()).first()
            
            if last_entry:
                parking_duration, parking_fee = self.calculate_parking_fee(
                    last_entry.access_time,
                    datetime.utcnow()
                )
        
        # Log successful access
        access_log = self.log_access(
            card.id,
            reader_id,
            access_type,
            AccessStatus.GRANTED,
            message
        )
        
        # Update parking info if exit
        if parking_duration is not None:
            access_log.parking_duration = parking_duration
            access_log.parking_fee = parking_fee
            self.db.commit()
        
        return {
            "access_granted": True,
            "message": message,
            "card_uid": card_uid,
            "vehicle_plate": card.vehicle_plate,
            "access_type": access_type.value,
            "parking_duration": parking_duration,
            "parking_fee": parking_fee
        }