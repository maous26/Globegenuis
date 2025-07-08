# backend/app/services/google_auth.py
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.core.config import settings
from app.utils.logger import logger


class GoogleAuthService:
    """Service for handling Google OAuth authentication"""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
    async def get_google_user_info(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for user information"""
        
        # Exchange code for access token
        token_data = await self._exchange_code_for_token(code)
        
        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        # Get user info from Google
        user_info = await self._get_user_info_from_google(token_data['access_token'])
        
        return user_info
    
    async def _exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None
    
    async def _get_user_info_from_google(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google using access token"""
        
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"Error getting user info from Google: {e}")
            raise HTTPException(status_code=400, detail="Failed to get user information")
    
    def get_google_auth_url(self) -> str:
        """Generate Google OAuth authorization URL"""
        
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'email profile',
            'access_type': 'offline'
        }
        
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"
