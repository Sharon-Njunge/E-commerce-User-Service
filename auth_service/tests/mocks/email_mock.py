from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class EmailMessage:
    id: str
    to: str
    subject: str
    body: str
    sent_at: datetime
    status: str  # sent, delivered, failed
    template: Optional[str] = None
    context: Optional[Dict] = None

class MockEmailService:
    def __init__(self):
        self.sent_emails: List[EmailMessage] = []
        self.failures_enabled = False
        self.delivery_delay = 0
        
    def send_email(self, to: str, subject: str, body: str, template: str = None, context: Dict = None) -> bool:
        """Send a mock email"""
        if self.failures_enabled:
            return False
            
        email = EmailMessage(
            id=f"email_{len(self.sent_emails) + 1}",
            to=to,
            subject=subject,
            body=body,
            sent_at=datetime.now(),
            status="sent",
            template=template,
            context=context
        )
        
        self.sent_emails.append(email)
        return True
    
    def send_verification_email(self, to: str, verification_url: str, user_name: str = "") -> bool:
        """Send email verification email"""
        subject = "Verify your email address"
        body = f"""
        Hello {user_name or 'User'},
        
        Please verify your email address by clicking the link below:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        """
        
        return self.send_email(
            to=to,
            subject=subject,
            body=body,
            template="verification",
            context={"verification_url": verification_url, "user_name": user_name}
        )
    
    def send_password_reset_email(self, to: str, reset_url: str, user_name: str = "") -> bool:
        """Send password reset email"""
        subject = "Reset your password"
        body = f"""
        Hello {user_name or 'User'},
        
        You requested to reset your password. Click the link below to proceed:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        """
        
        return self.send_email(
            to=to,
            subject=subject,
            body=body,
            template="password_reset",
            context={"reset_url": reset_url, "user_name": user_name}
        )
    
    def get_emails_sent_to(self, email: str) -> List[EmailMessage]:
        """Get all emails sent to a specific address"""
        return [email for email in self.sent_emails if email.to == email]
    
    def get_emails_by_template(self, template: str) -> List[EmailMessage]:
        """Get all emails sent using a specific template"""
        return [email for email in self.sent_emails if email.template == template]
    
    def clear_sent_emails(self):
        """Clear all sent emails (useful for tests)"""
        self.sent_emails.clear()
    
    def enable_failures(self):
        """Enable email sending failures for testing"""
        self.failures_enabled = True
    
    def disable_failures(self):
        """Disable email sending failures"""
        self.failures_enabled = False

# Global mock instance
mock_email_service = MockEmailService()