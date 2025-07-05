from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models import Alert
from app.schemas.alert import Alert as AlertSchema
from app.core.database import get_db

router = APIRouter()


@router.get("/", response_model=List[AlertSchema])
def get_user_alerts(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(deps.get_current_user)
):
    """Get user's alert history"""
    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id
    ).order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    
    return alerts