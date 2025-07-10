# backend/app/services/email_service.py
import os
from typing import Optional, Dict, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.core.config import settings
from app.utils.logger import logger

class EmailService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = Email(
            email=settings.SENDGRID_FROM_EMAIL,
            name=settings.SENDGRID_FROM_NAME
        )
        self.sg = SendGridAPIClient(self.api_key) if self.api_key else None
        
    async def send_admin_alert(self, subject: str, html_content: str, to_email: str) -> bool:
        """Send alert email to admin"""
        
        if not self.sg:
            logger.warning("SendGrid not configured, skipping email")
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.sg.send(message)
            
            if response.status_code == 202:
                logger.info(f"Admin alert sent to {to_email}: {subject}")
                return True
            else:
                logger.error(f"Failed to send admin alert. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending admin alert: {e}")
            return False