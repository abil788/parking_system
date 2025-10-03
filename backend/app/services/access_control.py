from sqlalchemy.orm import Session
from ..models import Card, Reader, AccessLog, AccessAction, AccessResult
from ..schemas.reader import ReaderEventResponse
from typing import Tuple


def process_access_event(
    db: Session,
    reader_id: str,
    card_uid: str,
    action: str
) -> Tuple[ReaderEventResponse, AccessLog]:
    """
    Process an access event from a reader device
    Returns tuple of (response, log_entry)
    """
    # Verify reader exists
    reader = db.query(Reader).filter(Reader.id == reader_id).first()
    if not reader:
        raise ValueError("Reader not found")
    
    # Find card by UID
    card = db.query(Card).filter(Card.card_uid == card_uid).first()
    
    # Determine action enum
    action_enum = AccessAction.ENTER if action == "enter" else AccessAction.EXIT
    
    # Card not found
    if not card:
        log = AccessLog(
            card_id=None,
            reader_id=reader.id,
            action=action_enum,
            result=AccessResult.DENIED,
            reason="not_found"
        )
        db.add(log)
        db.commit()
        
        response = ReaderEventResponse(
            result="denied",
            reason="not_found",
            message="Card not found in system"
        )
        return response, log
    
    # Check if card is valid
    if not card.is_valid():
        reason = card.get_denial_reason()
        log = AccessLog(
            card_id=card.id,
            reader_id=reader.id,
            action=action_enum,
            result=AccessResult.DENIED,
            reason=reason
        )
        db.add(log)
        db.commit()
        
        response = ReaderEventResponse(
            result="denied",
            reason=reason,
            message=f"Access denied: {reason}",
            owner_name=card.owner_name,
            vehicle_plate=card.vehicle_plate
        )
        return response, log
    
    # Access granted
    log = AccessLog(
        card_id=card.id,
        reader_id=reader.id,
        action=action_enum,
        result=AccessResult.GRANTED,
        reason=None
    )
    db.add(log)
    db.commit()
    
    action_text = "Entry" if action == "enter" else "Exit"
    response = ReaderEventResponse(
        result="granted",
        reason=None,
        message=f"{action_text} granted. Welcome {card.owner_name}",
        owner_name=card.owner_name,
        vehicle_plate=card.vehicle_plate
    )
    return response, log