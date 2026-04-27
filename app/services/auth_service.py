from sqlalchemy.orm import Session
from app_new.models.user import User
from app_new.core.security import verify_password, get_password_hash, create_access_token
from typing import Optional, Tuple
from pydantic import BaseModel

# Pydantic models for type safety
class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    department: str = "General"

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthService:
    
    @staticmethod
    def register(db: Session, user: RegisterRequest):
        """
        Register a new user in the database
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise ValueError("User already exists")
        
        # Create new user
        new_user = User(
            email=user.email,
            hashed_password=get_password_hash(user.password),
            first_name=user.first_name,
            last_name=user.last_name,
            department=user.department,
            role="user",
            name=f"{user.first_name} {user.last_name}"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user

    @staticmethod
    def login(db: Session, email: str, password: str) -> Tuple[str, User]:
        """
        Authenticate user and return token and user object
        """
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise ValueError("Invalid credentials")
        
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        
        # Create access token
        token = create_access_token({
            "sub": user.email, 
            "role": user.role,
            "user_id": user.id
        })
        
        return token, user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get user by email
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID
        """
        return db.query(User).filter(User.id == user_id).first()
