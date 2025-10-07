from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID
from ..database import get_db
from ..models import Reader, User
from ..schemas.reader import (
    ReaderCreate,
    ReaderUpdate,
    ReaderResponse,
    ReaderEventRequest,
    ReaderEventResponse
)
from ..services.access_control import process_access_event
from ..dependencies import get_current_user

router = APIRouter(prefix="/readers", tags=["Readers"])


@router.get("", response_model=list[ReaderResponse])
def list_readers(
    db: Session = Depends(get_db),
    # TEMPORARY: Disabled untuk testing
    # current_user: User = Depends(get_current_user)
):
    """List all readers"""
    readers = db.query(Reader).all()
    return [ReaderResponse.model_validate(reader) for reader in readers]


@router.post("", response_model=ReaderResponse, status_code=status.HTTP_201_CREATED)
def create_reader(
    reader_data: ReaderCreate,
    db: Session = Depends(get_db),
    # TEMPORARY: Disabled untuk testing
    # current_user: User = Depends(get_current_user)
):
    """Create a new reader"""
    new_reader = Reader(**reader_data.model_dump())
    db.add(new_reader)
    db.commit()
    db.refresh(new_reader)
    
    return ReaderResponse.model_validate(new_reader)


@router.get("/{reader_id}", response_model=ReaderResponse)
def get_reader(
    reader_id: UUID,
    db: Session = Depends(get_db),
    # TEMPORARY: Disabled untuk testing
    # current_user: User = Depends(get_current_user)
):
    """Get a specific reader by ID"""
    reader = db.query(Reader).filter(Reader.id == reader_id).first()
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found"
        )
    return ReaderResponse.model_validate(reader)


@router.put("/{reader_id}", response_model=ReaderResponse)
def update_reader(
    reader_id: UUID,
    reader_data: ReaderUpdate,
    db: Session = Depends(get_db),
    # TEMPORARY: Disabled untuk testing
    # current_user: User = Depends(get_current_user)
):
    """Update a reader"""
    reader = db.query(Reader).filter(Reader.id == reader_id).first()
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found"
        )
    
    # Update only provided fields
    update_data = reader_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reader, field, value)
    
    db.commit()
    db.refresh(reader)
    
    return ReaderResponse.model_validate(reader)


@router.post("/{reader_id}/event", response_model=ReaderEventResponse)
async def process_reader_event(
    request: Request,  # ← TAMBAH INI
    reader_id: UUID,
    event_data: ReaderEventRequest,
    db: Session = Depends(get_db)
):
    """
    Process an access event from a reader device
    This endpoint does NOT require authentication (for device usage)
    
    INI YANG DIPANGGIL SAAT RFID SCAN!
    """
    try:
        # Process the access event
        response, log = process_access_event(
            db=db,
            reader_id=str(reader_id),
            card_uid=event_data.card_uid,
            action=event_data.action
        )
        
        # BROADCAST TO WEBSOCKET CLIENTS
        try:
            ws_manager = request.app.state.ws_manager
            
            # Refresh log to load relationships
            db.refresh(log)
            
            broadcast_data = {
                "id": str(log.id),
                "card_id": str(log.card_id) if log.card_id else None,
                "reader_id": str(log.reader_id),
                "card_uid": event_data.card_uid,
                "timestamp": log.timestamp.isoformat(),
                "action": log.action.value,
                "result": log.result.value,
                "reason": log.reason,
                "owner_name": response.owner_name if response.owner_name else None,
                "vehicle_plate": response.vehicle_plate if response.vehicle_plate else None,
                "reader_location": log.reader.location if log.reader else None,
                "reader_type": log.reader.type.value if log.reader else None,
            }
            
            # Broadcast asynchronously
            await ws_manager.broadcast(broadcast_data)
            print(f"📡 Broadcasted: {event_data.card_uid} - {log.result.value}")
            
        except Exception as e:
            # Log error but don't fail the request
            print(f"❌ WebSocket broadcast error: {e}")
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ Error processing event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing event: {str(e)}"
        )