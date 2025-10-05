from sqlalchemy.orm import Session
from ..models import Card, Reader, AccessLog, AccessAction, AccessResult
from ..schemas.reader import ReaderEventResponse
from ..cache import get_cache, set_cache, delete_cache
from typing import Tuple
from typing import Tuple
import asyncio
import json


def get_card_cached(db: Session, card_uid: str) -> Card:
    """Get card from cache or database"""
    cache_key = f"card:{card_uid}"
    
    # Try cache first
    cached_data = get_cache(cache_key)
    if cached_data:
        # Reconstruct card object
        card = Card(
            id=cached_data['id'],
            card_uid=cached_data['card_uid'],
            owner_name=cached_data['owner_name'],
            vehicle_plate=cached_data['vehicle_plate'],
            status=cached_data['status'],
            issued_at=cached_data['issued_at'],
            expires_at=cached_data.get('expires_at')
        )
        return card
    
    # Cache miss - query database
    card = db.query(Card).filter(Card.card_uid == card_uid).first()
    
    if card:
        # Cache the result
        card_data = {
            'id': str(card.id),
            'card_uid': card.card_uid,
            'owner_name': card.owner_name,
            'vehicle_plate': card.vehicle_plate,
            'status': card.status.value,
            'issued_at': card.issued_at.isoformat(),
            'expires_at': card.expires_at.isoformat() if card.expires_at else None
        }
        set_cache(cache_key, card_data, ttl=300)  # Cache 5 minutes
    
    return card


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
    # Verify reader exists (could also be cached)
    reader = db.query(Reader).filter(Reader.id == reader_id).first()
    if not reader:
        raise ValueError("Reader not found")
    
    # Find card by UID (with cache)
    card = get_card_cached(db, card_uid)
    
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