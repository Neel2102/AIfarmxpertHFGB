"""
Email Service
Handles sending emails for password reset and notifications
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from farmxpert.config.settings import get_settings

settings = get_settings()

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        # For development, we'll use a simple console-based email service
        # In production, you would configure SMTP settings
        self.smtp_server = "smtp.gmail.com"  # Example SMTP server
        self.smtp_port = 587
        self.sender_email = "noreply@farmxpert.com"  # Your email
        self.sender_password = ""  # Your email password or app password
    
    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> bool:
        """Send password reset email"""
        try:
            # For development, we'll just print the reset link
            # In production, you would send an actual email
            reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
            
            print(f"\n{'='*60}")
            print(f"PASSWORD RESET EMAIL (Development Mode)")
            print(f"{'='*60}")
            print(f"To: {to_email}")
            print(f"Subject: Reset Your FarmXpert Password")
            print(f"\nHello {user_name},")
            print(f"\nYou requested a password reset for your FarmXpert account.")
            print(f"Click the link below to reset your password:")
            print(f"\n{reset_url}")
            print(f"\nThis link will expire in 1 hour.")
            print(f"If you didn't request this, please ignore this email.")
            print(f"\nBest regards,")
            print(f"The FarmXpert Team")
            print(f"{'='*60}\n")
            
            # In production, you would send the actual email here
            # return self._send_actual_email(to_email, subject, body)
            
            return True
            
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return False
    
    def _send_actual_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send actual email via SMTP (for production)"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email
            
            # Create HTML and plain text versions
            text_part = MIMEText(body, "plain")
            html_part = MIMEText(body.replace('\n', '<br>'), "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

# Global instance
email_service = EmailService()
