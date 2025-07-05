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
            
            message = Mail(
                from_email=self.from_email,
                to_emails=To(user.email, f"{user.first_name or 'Voyageur'}"),
                subject=subject,
                html_content=html_content
            )
            
            # Add tracking
            message.tracking_settings = {
                "click_tracking": {"enable": True},
                "open_tracking": {"enable": True}
            }
            
            # Send
            response = self.sg.send(message)
            
            logger.info(f"Alert sent to {user.email}: {response.status_code}")
            
            return response.headers.get("X-Message-Id")
            
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
            
            deal_list.append({
                "origin": route.origin,
                "destination": route.destination,
                "price": deal.deal_price,
                "normal_price": deal.normal_price,
                "discount_percentage": int(deal.discount_percentage),
                "savings": savings,
                "is_error_fare": deal.is_error_fare,
                "expires_in_hours": int((deal.expires_at - datetime.now()).total_seconds() / 3600)
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