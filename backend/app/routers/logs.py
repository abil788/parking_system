from fastapi import APIRouter, Depends, Query, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, date
from typing import Optional
from uuid import UUID
import csv
import io
from ..database import get_db
from ..models import AccessLog, Card, Reader, User, AccessResult, AccessAction
from ..schemas.access_log import AccessLogResponse, AccessLogListResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/logs", tags=["Access Logs"])


async def broadcast_new_log(request: Request, log: AccessLog):
    """Helper function to broadcast new log to all WebSocket clients"""
    try:
        ws_manager = request.app.state.ws_manager
        
        # Format data untuk frontend
        log_data = {
            "id": str(log.id),
            "card_id": str(log.card_id) if log.card_id else None,
            "reader_id": str(log.reader_id),
            "timestamp": log.timestamp.isoformat(),
            "action": log.action.value if log.action else None,
            "result": log.result.value if log.result else None,
            "reason": log.reason,
            "card_uid": log.card.card_uid if log.card else None,
            "owner_name": log.card.owner_name if log.card else None,
            "vehicle_plate": log.card.vehicle_plate if log.card else None,
            "reader_location": log.reader.location if log.reader else None,
            "reader_type": log.reader.type.value if log.reader else None,
        }
        
        await ws_manager.broadcast(log_data)
        print(f"📡 Broadcasted new log: {log_data.get('card_uid')} - {log_data.get('result')}")
    except Exception as e:
        print(f"❌ Error broadcasting log: {e}")


@router.get("", response_model=AccessLogListResponse)
async def list_logs(
    request: Request,  # ADD THIS untuk akses ws_manager
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    card_id: Optional[UUID] = None,
    reader_id: Optional[UUID] = None,
    result: Optional[AccessResult] = None,
    action: Optional[AccessAction] = None,
    db: Session = Depends(get_db),
    # TEMPORARY: Comment out authentication untuk testing
    # current_user: User = Depends(get_current_user)
):
    """List access logs with filtering and pagination"""
    query = db.query(AccessLog).join(Reader, AccessLog.reader_id == Reader.id)
    query = query.outerjoin(Card, AccessLog.card_id == Card.id)
    
    # Apply filters
    filters = []
    if start_date:
        filters.append(AccessLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        filters.append(AccessLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
    if card_id:
        filters.append(AccessLog.card_id == card_id)
    if reader_id:
        filters.append(AccessLog.reader_id == reader_id)
    if result:
        filters.append(AccessLog.result == result)
    if action:
        filters.append(AccessLog.action == action)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Order by timestamp desc
    query = query.order_by(AccessLog.timestamp.desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Build response with additional data
    log_responses = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "card_id": log.card_id,
            "reader_id": log.reader_id,
            "timestamp": log.timestamp,
            "action": log.action,
            "result": log.result,
            "reason": log.reason,
            "card_uid": log.card.card_uid if log.card else None,
            "owner_name": log.card.owner_name if log.card else None,
            "vehicle_plate": log.card.vehicle_plate if log.card else None,
            "reader_location": log.reader.location if log.reader else None,
            "reader_type": log.reader.type.value if log.reader else None,
        }
        log_responses.append(AccessLogResponse(**log_dict))
    
    return AccessLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        logs=log_responses
    )


@router.get("/export/csv")
def export_logs_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    card_id: Optional[UUID] = None,
    reader_id: Optional[UUID] = None,
    result: Optional[AccessResult] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export access logs to CSV"""
    query = db.query(AccessLog).join(Reader, AccessLog.reader_id == Reader.id)
    query = query.outerjoin(Card, AccessLog.card_id == Card.id)
    
    # Apply filters (same as list_logs)
    filters = []
    if start_date:
        filters.append(AccessLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        filters.append(AccessLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
    if card_id:
        filters.append(AccessLog.card_id == card_id)
    if reader_id:
        filters.append(AccessLog.reader_id == reader_id)
    if result:
        filters.append(AccessLog.result == result)
    
    if filters:
        query = query.filter(and_(*filters))
    
    query = query.order_by(AccessLog.timestamp.desc())
    logs = query.all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Timestamp", "Card UID", "Owner Name", "Vehicle Plate",
        "Reader Location", "Action", "Result", "Reason"
    ])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            log.card.card_uid if log.card else "N/A",
            log.card.owner_name if log.card else "N/A",
            log.card.vehicle_plate if log.card else "N/A",
            log.reader.location if log.reader else "N/A",
            log.action.value,
            log.result.value,
            log.reason or ""
        ])
    
    # Return CSV response
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=access_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


# ============================================
# HELPER FUNCTION untuk RFID Reader
# ============================================
async def create_and_broadcast_log(
    request: Request,
    db: Session,
    card_id: Optional[UUID],
    reader_id: UUID,
    action: AccessAction,
    result: AccessResult,
    reason: Optional[str] = None
) -> AccessLog:
    """
    Create access log and broadcast to WebSocket clients
    
    GUNAKAN FUNCTION INI di RFID reader integration Anda!
    
    Example usage:
    ```python
    from app.routers.logs import create_and_broadcast_log
    
    # Di RFID reader code:
    log = await create_and_broadcast_log(
        request=request,
        db=db,
        card_id=card.id if card else None,
        reader_id=reader.id,
        action=AccessAction.ENTER,
        result=AccessResult.GRANTED if valid else AccessResult.DENIED,
        reason="Card not found" if not valid else None
    )
    ```
    """
    
    # Create log
    new_log = AccessLog(
        card_id=card_id,
        reader_id=reader_id,
        action=action,
        result=result,
        reason=reason,
        timestamp=datetime.now()
    )
    
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    # Load relationships untuk broadcast
    db.refresh(new_log)
    if new_log.card_id:
        _ = new_log.card  # Force load card relationship
    _ = new_log.reader  # Force load reader relationship
    
    # Broadcast to all WebSocket clients
    await broadcast_new_log(request, new_log)
    
    return new_log


# ============================================
# TEST ENDPOINT - untuk testing WebSocket
# ============================================
@router.post("/test/create")
async def create_test_log(
    request: Request,
    card_id: Optional[UUID] = None,
    reader_id: Optional[UUID] = None,
    action: AccessAction = AccessAction.ENTER,
    result: AccessResult = AccessResult.GRANTED,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    TEST ENDPOINT: Create a test log and broadcast to WebSocket
    
    Untuk testing, bisa gunakan:
    - card_id: ambil dari database cards
    - reader_id: ambil dari database readers
    
    Jika tidak ada, akan create log tanpa card
    """
    
    # Jika tidak ada reader_id, ambil reader pertama
    if not reader_id:
        reader = db.query(Reader).first()
        if not reader:
            return {"error": "No readers found in database"}
        reader_id = reader.id
    
    # Create and broadcast log
    log = await create_and_broadcast_log(
        request=request,
        db=db,
        card_id=card_id,
        reader_id=reader_id,
        action=action,
        result=result,
        reason=reason
    )
    
    return {
        "success": True,
        "message": "Test log created and broadcasted",
        "log_id": str(log.id),
        "broadcasted": True
    }


# ============================================
# DEBUG ENDPOINT - untuk cek authentication
# ============================================
@router.get("/debug/auth")
async def debug_auth(
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to check if authentication works"""
    return {
        "authenticated": True,
        "user_id": str(current_user.id),
        "username": current_user.username,
        "message": "Authentication is working!"
    }