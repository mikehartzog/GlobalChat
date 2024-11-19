from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from app import models, schemas, auth
from app.database import get_db
from datetime import timedelta
from typing import Optional

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(
        (models.User.email == user.email) | 
        (models.User.username == user.username)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email or username already registered"
        )
    
    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        preferred_language=user.preferred_language
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=schemas.Token)
async def login(
    email_or_username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, email_or_username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# Add a test endpoint to verify authentication
@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user = Depends(auth.get_current_user)):
    return current_user



@router.patch("/settings")
async def update_user_settings(
    auto_translate: Optional[bool] = None,
    preferred_language: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if auto_translate is not None:
        current_user.auto_translate = auto_translate
    if preferred_language is not None:
        current_user.preferred_language = preferred_language
    
    db.commit()
    return {
        "auto_translate": current_user.auto_translate,
        "preferred_language": current_user.preferred_language
    }


@router.get("/settings")
async def get_user_settings(
    current_user: models.User = Depends(auth.get_current_user)
):
    return {
        "auto_translate": current_user.auto_translate,
        "preferred_language": current_user.preferred_language
    }