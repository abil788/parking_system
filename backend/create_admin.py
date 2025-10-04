"""
Script to create initial superadmin user
Run: python create_admin.py
"""
from app.database import SessionLocal
from app.models import User, UserRole
from app.services.auth import get_password_hash
import sys
import uuid


def create_superadmin():
    db = SessionLocal()
    
    try:
        # Check if superadmin exists
        existing = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
        if existing:
            print(f"Superadmin already exists: {existing.username}")
            return
        
        # Get input
        username = input("Enter superadmin username: ").strip()
        if not username:
            print("Username cannot be empty")
            sys.exit(1)
        
        email = input("Enter superadmin email: ").strip()
        if not email:
            print("Email cannot be empty")
            sys.exit(1)
        
        password = input("Enter superadmin password (min 6 chars): ").strip()
        if len(password) < 6:
            print("Password must be at least 6 characters")
            sys.exit(1)
        
        # Create superadmin
        superadmin = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=UserRole.SUPERADMIN
        )
        
        db.add(superadmin)
        db.commit()
        
        print(f"\n✓ Superadmin created successfully!")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print("You can now login to the system.")
        
    except Exception as e:
        print(f"Error creating superadmin: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_superadmin()