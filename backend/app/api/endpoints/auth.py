from datetime import timedelta, datetime, datetime
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import models, schemas
from app.core import security
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.post("/login", response_model=schemas.Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login"""
    user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()
    
    if not user or not security.verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password"
        )
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    return {
        "access_token": security.create_access_token(
            user.email, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/forgot-password", response_model=schemas.PasswordResetResponse)
def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db)
) -> Any:
    """Request password reset"""
    user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()
    
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "Si cet email existe, vous recevrez un lien de réinitialisation"}
    
    if not user.is_active:
        return {"message": "Si cet email existe, vous recevrez un lien de réinitialisation"}
    
    # Generate reset token
    reset_token = security.generate_reset_token()
    reset_token_expires = datetime.utcnow() + timedelta(hours=24)
    
    # Save token to database
    user.reset_token = reset_token
    user.reset_token_expires_at = reset_token_expires
    db.commit()
    
    # Send reset email
    from app.services.email_service import EmailService
    email_service = EmailService()
    email_service.send_password_reset_email(user, reset_token)
    
    return {"message": "Si cet email existe, vous recevrez un lien de réinitialisation"}


@router.post("/reset-password", response_model=schemas.PasswordResetResponse)
def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
) -> Any:
    """Reset password with token"""
    # Find user by token
    user = db.query(models.User).filter(
        models.User.reset_token == request.token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Token invalide ou expiré"
        )
    
    # Check if token is expired
    if not user.reset_token_expires_at or user.reset_token_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Token expiré"
        )
    
    # Update password
    user.hashed_password = security.get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()
    
    return {"message": "Mot de passe réinitialisé avec succès"}


@router.post("/verify-reset-token")
def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """Verify if reset token is valid"""
    user = db.query(models.User).filter(
        models.User.reset_token == token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Token invalide"
        )
    
    if not user.reset_token_expires_at or user.reset_token_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Token expiré"
        )
    
    return {"message": "Token valide", "email": user.email}