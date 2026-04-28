from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from app_new.models.user import User
from app_new.core.security import hash_password, verify_password, create_token
from app_new.core.deps import get_current_user
import traceback

router = APIRouter(tags=["Auth"])

@router.post("/register")
def register(user: dict, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    try:
        existing = db.query(User).filter(User.email == user["email"]).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        
        new_user = User(
            email=user["email"],
            hashed_password=hash_password(user["password"]),
            first_name=user.get("first_name", ""),
            last_name=user.get("last_name", ""),
            department=user.get("department", "General"),
            role="user",
            name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        )
        
        db.add(new_user)
        db.commit()
        
        return {"message": "User created successfully"}
    except Exception as e:
        print("🔥 REGISTER ERROR:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(user: dict, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token
    """
    db_user = db.query(User).filter(User.email == user["email"]).first()
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(user["password"], db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token({
        "sub": db_user.email,
        "role": db_user.role
    })
    
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "name": current_user.name,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "department": current_user.department
    }
