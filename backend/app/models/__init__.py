from app.models.user import User, UserTier
from app.models.flight import Route, PriceHistory, Deal
from app.models.alert import Alert, AlertPreference

__all__ = [
    "User", "UserTier",
    "Route", "PriceHistory", "Deal",
    "Alert", "AlertPreference"
]