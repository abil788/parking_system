from fastapi import APIRouter, Depends, Query, Response
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


@router.get("", response_model=AccessLogListResponse)
def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    card_id: Optional[UUID] = None,
    reader_id: Optional[UUID] = None,
    result: Optional[AccessResult] = None,
    action: Optional[AccessAction] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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