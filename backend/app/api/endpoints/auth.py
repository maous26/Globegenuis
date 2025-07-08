from datetime import timedelta, datetime
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import models, schemas
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.services.google_auth import GoogleAuthService
from app.utils.logger import logger

router = APIRouter()


@router.get("/google/url")
def get_google_auth_url():
    """Get Google OAuth authorization URL"""
    google_service = GoogleAuthService()
    auth_url = google_service.get_google_auth_url()
    return {"auth_url": auth_url}


@router.post("/google/callback")
async def google_callback(
    code: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    google_service = GoogleAuthService()
    
    try:
        # Get user info from Google
        google_user = await google_service.get_google_user_info(code)
        
        # Check if user exists
        existing_user = db.query(models.User).filter(
            models.User.google_id == google_user['id']
        ).first()
        
        if not existing_user:
            # Check if user exists with same email
            existing_user = db.query(models.User).filter(
                models.User.email == google_user['email']
            ).first()
            
            if existing_user:
                # Link Google account to existing user
                existing_user.google_id = google_user['id']
                existing_user.auth_provider = "google"
                existing_user.profile_picture = google_user.get('picture')
                existing_user.is_verified = True
            else:
                # Create new user
                existing_user = models.User(
                    email=google_user['email'],
                    first_name=google_user.get('given_name', ''),
                    last_name=google_user.get('family_name', ''),
                    google_id=google_user['id'],
                    auth_provider="google",
                    profile_picture=google_user.get('picture'),
                    is_verified=True,
                    hashed_password=""  # No password for Google users
                )
                db.add(existing_user)
        
        # Update last login
        existing_user.last_login_at = datetime.now()
        db.commit()
        
        # Create access token
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        access_token = security.create_access_token(
            existing_user.email, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": existing_user.id,
                "email": existing_user.email,
                "first_name": existing_user.first_name,
                "last_name": existing_user.last_name,
                "profile_picture": existing_user.profile_picture,
                "tier": existing_user.tier.value,
                "is_admin": existing_user.is_admin
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests"""
    try:
        # Find user by email (username field in OAuth2 form)
        user = db.query(models.User).filter(
            models.User.email == form_data.username
        ).first()
        
        if not user:
            logger.warning(f"Login attempt for non-existent user: {form_data.username}")
            raise HTTPException(
                status_code=400,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {form_data.username}")
            raise HTTPException(
                status_code=400,
                detail="Inactive user"
            )
        
        # Verify password
        if not security.verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Invalid password attempt for user: {form_data.username}")
            raise HTTPException(
                status_code=400,
                detail="Incorrect email or password"
            )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=60 * 24 * 7)  # 7 days
        access_token = security.create_access_token(
            user.email, expires_delta=access_token_expires
        )
        
        logger.info(f"Successful login for user: {user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 60 * 24 * 7 * 60,  # 7 days in seconds
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_picture": user.profile_picture,
                "tier": user.tier.value if user.tier else "free",
                "is_admin": user.is_admin,
                "is_superadmin": user.is_superadmin,
                "is_verified": user.is_verified,
                "onboarding_completed": user.onboarding_completed
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during login"
        )


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