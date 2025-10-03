from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
from typing import Optional
from ..database import get_db
from ..models import Card, CardStatus, User
from ..schemas.card import CardCreate, CardUpdate, CardResponse, CardListResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/cards", tags=["Cards"])


@router.get("", response_model=CardListResponse)
def list_cards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[CardStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all cards with pagination and filtering"""
    query = db.query(Card)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Card.card_uid.ilike(f"%{search}%"),
                Card.owner_name.ilike(f"%{search}%"),
                Card.vehicle_plate.ilike(f"%{search}%")
            )
        )
    
    if status:
        query = query.filter(Card.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    cards = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return CardListResponse(
        total=total,
        page=page,
        page_size=page_size,
        cards=[CardResponse.model_validate(card) for card in cards]
    )


@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    card_data: CardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new card"""
    # Check if card_uid already exists
    existing_card = db.query(Card).filter(Card.card_uid == card_data.card_uid).first()
    if existing_card:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Card UID already exists"
        )
    
    new_card = Card(**card_data.model_dump())
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    
    return CardResponse.model_validate(new_card)


@router.get("/{card_id}", response_model=CardResponse)
def get_card(
    card_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific card by ID"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return CardResponse.model_validate(card)


@router.put("/{card_id}", response_model=CardResponse)
def update_card(
    card_id: UUID,
    card_data: CardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a card"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Update only provided fields
    update_data = card_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(card, field, value)
    
    db.commit()
    db.refresh(card)
    
    return CardResponse.model_validate(card)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a card"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    db.delete(card)
    db.commit()
    
    return None