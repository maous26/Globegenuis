from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
from app.core.security import get_password_hash  # Import the function directly
from app.core import security
from app.core.database import get_db

router = APIRouter()


@router.post("/signup", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate
) -> Any:
    """Create new user with email only (step 1 of onboarding)"""
    # Check if user exists
    user = db.query(models.User).filter(
        models.User.email == user_in.email
    ).first()
    
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists"
        )
    
    # Create user
    user = models.User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),  # Use directly imported function
        onboarding_step=1
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create default alert preferences
    alert_prefs = models.AlertPreference(user_id=user.id)
    db.add(alert_prefs)
    db.commit()
    
    return user


@router.put("/me/onboarding", response_model=schemas.User)
def update_onboarding(
    *,
    db: Session = Depends(get_db),
    onboarding_data: schemas.UserOnboarding,
    current_user: models.User = Depends(deps.get_current_user)
) -> Any:
    """Update user onboarding progress"""
    
    # Process based on step
    if onboarding_data.step == 2:
        # Step 2: Name and home city
        current_user.first_name = onboarding_data.data.get("first_name")
        current_user.home_airports = onboarding_data.data.get("home_airports", [])
        
    elif onboarding_data.step == 3:
        # Step 3: Travel preferences
        current_user.travel_types = onboarding_data.data.get("travel_types", [])
        
    elif onboarding_data.step == 4:
        # Step 4: Favorite destinations
        current_user.favorite_destinations = onboarding_data.data.get(
            "favorite_destinations", []
        )
        
    elif onboarding_data.step == 5:
        # Step 5: Complete profile
        current_user.onboarding_completed = True
    
    # Update step
    current_user.onboarding_step = onboarding_data.step
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/me", response_model=schemas.User)
def read_user_me(
    current_user: models.User = Depends(deps.get_current_user)
) -> Any:
    """Get current user"""
    return current_user


@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_user)
) -> Any:
    """Update current user"""
    for field, value in user_in.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/me/alert-preferences", response_model=schemas.AlertPreference)
def get_alert_preferences(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
) -> Any:
    """Get user's alert preferences"""
    prefs = db.query(models.AlertPreference).filter(
        models.AlertPreference.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create default preferences
        prefs = models.AlertPreference(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return prefs


@router.put("/me/alert-preferences", response_model=schemas.AlertPreference)
def update_alert_preferences(
    *,
    db: Session = Depends(get_db),
    prefs_in: schemas.AlertPreferenceUpdate,
    current_user: models.User = Depends(deps.get_current_user)
) -> Any:
    """Update user's alert preferences"""
    prefs = db.query(models.AlertPreference).filter(
        models.AlertPreference.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = models.AlertPreference(user_id=current_user.id)
        db.add(prefs)
    
    for field, value in prefs_in.dict(exclude_unset=True).items():
        setattr(prefs, field, value)
    
    db.commit()
    db.refresh(prefs)
    
    return prefs