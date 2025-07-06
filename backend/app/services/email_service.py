from typing import List, Dict, Any, Optional
from datetime import datetime
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from jinja2 import Template
from app.core.config import settings
from app.models import User, Deal, Alert
from app.utils.logger import logger


class EmailService:
    def __init__(self):
        self.sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        self.from_email = Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME)
        
    def send_deal_alert(
        self,
        user: User,
        deals: List[Deal],
        alert_type: str = "instant"
    ) -> Optional[str]:
        """Send deal alert email to user"""
        try:
            # Prepare template data
            template_data = self._prepare_deal_data(deals, user)
            
            # Create email
            subject = self._generate_subject(deals)
            html_content = self._render_deal_template(template_data)
            
            # Fix for SendGrid API changes
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            message = Mail(
                from_email=(self.from_email.email, self.from_email.name),
                to_emails=(user.email, f"{user.first_name or 'Voyageur'}"),
                subject=subject,
                html_content=html_content
            )
            
            # Send with explicit parameters
            import json
            from python_http_client.client import Response
            
            data = message.get()
            response = self.sg.client.mail.send.post(request_body=data)
            
            logger.info(f"Alert sent to {user.email}: {response.status_code}")
            
            # Handle response correctly for both success status codes
            if response.status_code == 202:  # SendGrid success status code
                if hasattr(response, 'headers') and isinstance(response.headers, dict):
                    return response.headers.get("X-Message-Id", "sent-but-no-id")
                else:
                    return "sent-successfully"  # Return a value to indicate success
            else:
                logger.error(f"SendGrid API returned non-success status code: {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"Error sending email to {user.email}: {e}")
            return None
    
    def send_welcome_email(self, user: User) -> Optional[str]:
        """Send welcome email after signup"""
        try:
            subject = "Bienvenue sur GlobeGenius ! 🚀"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #1a1a1a;">Bienvenue {user.first_name or 'Voyageur'} !</h1>
                
                <p>Merci de rejoindre GlobeGenius, votre assistant intelligent pour dénicher 
                les meilleures erreurs de prix et deals voyage.</p>
                
                <h2>🎯 Prochaines étapes :</h2>
                <ol>
                    <li>Complétez votre profil pour recevoir des alertes personnalisées</li>
                    <li>Sélectionnez vos aéroports de départ préférés</li>
                    <li>Choisissez vos destinations favorites</li>
                </ol>
                
                <p>Notre IA scanne en permanence des milliers de vols pour vous trouver 
                des deals jusqu'à -80% !</p>
                
                <a href="https://app.globegenius.com/onboarding" 
                   style="display: inline-block; background: #007bff; color: white; 
                          padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                    Compléter mon profil
                </a>
                
                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    L'équipe GlobeGenius<br>
                    <a href="https://globegenius.com">globegenius.com</a>
                </p>
            </div>
            """
            
            message = Mail(
                from_email=self.from_email,
                to_emails=user.email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.sg.send(message)
            return response.headers.get("X-Message-Id")
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return None
    
    def _prepare_deal_data(self, deals: List[Deal], user: User) -> Dict[str, Any]:
        """Prepare deal data for email template"""
        deal_list = []
        total_savings = 0
        
        for deal in deals[:10]:  # Limit to 10 deals per email
            route = deal.route
            savings = deal.normal_price - deal.deal_price
            total_savings += savings
            
            # Fix for datetime timezone issue
            import pytz
            now = datetime.now(pytz.UTC)
            expires_at = deal.expires_at
            if expires_at.tzinfo is None:
                expires_at = pytz.UTC.localize(expires_at)
            
            hours_diff = max(0, int((expires_at - now).total_seconds() / 3600))
            
            deal_list.append({
                "origin": route.origin,
                "destination": route.destination,
                "price": deal.deal_price,
                "normal_price": deal.normal_price,
                "discount_percentage": int(deal.discount_percentage),
                "savings": savings,
                "is_error_fare": deal.is_error_fare,
                "expires_in_hours": hours_diff,
                "id": deal.id
            })
        
        return {
            "user_name": user.first_name or "Voyageur",
            "deals": deal_list,
            "total_deals": len(deals),
            "total_savings": total_savings,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
    
    def _generate_subject(self, deals: List[Deal]) -> str:
        """Generate email subject based on deals"""
        if not deals:
            return "GlobeGenius - Nouvelles alertes voyage"
        
        best_deal = max(deals, key=lambda d: d.discount_percentage)
        
        if best_deal.is_error_fare:
            return f"🚨 ERREUR DE PRIX: {best_deal.route.origin}→{best_deal.route.destination} -{int(best_deal.discount_percentage)}% !"
        elif best_deal.discount_percentage >= 50:
            return f"⚡ Deal exceptionnel: -{int(best_deal.discount_percentage)}% sur {best_deal.route.destination}"
        else:
            return f"✈️ {len(deals)} nouveaux deals jusqu'à -{int(best_deal.discount_percentage)}%"
    
    def _render_deal_template(self, data: Dict[str, Any]) -> str:
        """Render HTML email template"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #007bff; color: white; padding: 20px; text-align: center; }
                .deal-card { 
                    border: 1px solid #ddd; 
                    padding: 15px; 
                    margin: 15px 0; 
                    border-radius: 8px;
                    background: #f9f9f9;
                }
                .error-fare { border-color: #ff4444; background: #fff5f5; }
                .price { font-size: 24px; font-weight: bold; color: #007bff; }
                .original-price { text-decoration: line-through; color: #999; }
                .discount { 
                    background: #28a745; 
                    color: white; 
                    padding: 4px 8px; 
                    border-radius: 4px;
                    display: inline-block;
                }
                .cta-button {
                    display: inline-block;
                    background: #007bff;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 10px 0;
                }
                .footer { 
                    margin-top: 40px; 
                    padding-top: 20px; 
                    border-top: 1px solid #ddd;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>GlobeGenius</h1>
                    <p>{{ total_deals }} nouveaux deals détectés !</p>
                </div>
                
                <p>Bonjour {{ user_name }},</p>
                
                <p>Notre IA a détecté <strong>{{ total_deals }} nouveaux deals</strong> 
                   avec un potentiel d'économie total de <strong>{{ total_savings }}€</strong> !</p>
                
                {% for deal in deals %}
                <div class="deal-card {% if deal.is_error_fare %}error-fare{% endif %}">
                    {% if deal.is_error_fare %}
                    <span style="color: #ff4444; font-weight: bold;">🚨 ERREUR DE PRIX DÉTECTÉE</span>
                    {% endif %}
                    
                    <h3>{{ deal.origin }} → {{ deal.destination }}</h3>
                    
                    <div>
                        <span class="price">{{ deal.price }}€</span>
                        <span class="original-price">{{ deal.normal_price }}€</span>
                        <span class="discount">-{{ deal.discount_percentage }}%</span>
                    </div>
                    
                    <p>Économie: <strong>{{ deal.savings }}€</strong></p>
                    
                    {% if deal.expires_in_hours < 24 %}
                    <p style="color: #ff6b6b;">⏱️ Expire dans {{ deal.expires_in_hours }}h !</p>
                    {% endif %}
                    
                    <a href="https://app.globegenius.com/deal/{{ deal.id }}" class="cta-button">
                        Voir le deal
                    </a>
                </div>
                {% endfor %}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.globegenius.com/deals" class="cta-button">
                        Voir tous les deals
                    </a>
                </div>
                
                <div class="footer">
                    <p>Vous recevez cet email car vous êtes inscrit à GlobeGenius.</p>
                    <p>
                        <a href="https://app.globegenius.com/preferences">Gérer mes préférences</a> |
                        <a href="https://app.globegenius.com/unsubscribe">Se désinscrire</a>
                    </p>
                    <p>© 2024 GlobeGenius. Tous droits réservés.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return Template(template).render(**data)
    
    def send_password_reset_email(self, user: User, reset_token: str) -> Optional[str]:
        """Send password reset email to user"""
        try:
            # Create reset URL
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            
            # Prepare email content
            subject = "Réinitialisation de votre mot de passe - GlobeGenius"
            html_content = self._render_reset_password_template({
                "user_name": user.first_name or user.email.split('@')[0],
                "reset_url": reset_url,
                "expiry_hours": 24
            })
            
            message = Mail(
                from_email=self.from_email,
                to_emails=To(user.email, f"{user.first_name or 'Voyageur'}"),
                subject=subject,
                html_content=html_content
            )
            
            # Send email
            response = self.sg.send(message)
            
            logger.info(f"Password reset email sent to {user.email}: {response.status_code}")
            
            return response.headers.get("X-Message-Id")
            
        except Exception as e:
            logger.error(f"Error sending password reset email to {user.email}: {str(e)}")
            return None
    
    def _render_reset_password_template(self, data: Dict[str, Any]) -> str:
        """Render password reset email template"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Réinitialisation de mot de passe</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .cta-button { display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }
                .footer { text-align: center; margin-top: 30px; color: #666; font-size: 14px; }
                .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Réinitialisation de mot de passe</h1>
                    <p>GlobeGenius</p>
                </div>
                
                <div class="content">
                    <p>Bonjour {{ user_name }},</p>
                    
                    <p>Nous avons reçu une demande de réinitialisation de mot de passe pour votre compte GlobeGenius.</p>
                    
                    <p>Pour réinitialiser votre mot de passe, cliquez sur le bouton ci-dessous :</p>
                    
                    <div style="text-align: center;">
                        <a href="{{ reset_url }}" class="cta-button">
                            Réinitialiser mon mot de passe
                        </a>
                    </div>
                    
                    <div class="warning">
                        <p><strong>⚠️ Important :</strong></p>
                        <ul>
                            <li>Ce lien est valable pendant {{ expiry_hours }} heures seulement</li>
                            <li>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email</li>
                            <li>Votre mot de passe actuel reste inchangé tant que vous ne créez pas un nouveau mot de passe</li>
                        </ul>
                    </div>
                    
                    <p>Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :</p>
                    <p style="word-break: break-all; color: #667eea;">{{ reset_url }}</p>
                </div>
                
                <div class="footer">
                    <p>Vous recevez cet email car une réinitialisation de mot de passe a été demandée pour votre compte GlobeGenius.</p>
                    <p>© 2024 GlobeGenius. Tous droits réservés.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return Template(template).render(**data)