import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from core.config import settings
import uuid

class EmailService:
    def __init__(self):
        # We try to initialize SendGrid but don't crash if the key is just a placeholder
        self.api_key = settings.SENDGRID_API_KEY
        self.client = SendGridAPIClient(self.api_key) if "placeholder" not in self.api_key else None
        
        # In a real app, this should be your actual domain or localhost for testing
        self.base_url = "http://localhost:8000"

    def send_verification_email(self, to_email: str, user_id: str):
        """Generates a UUID token and sends the Yes/No email"""
        
        # 1. Generate unique security tokens for both buttons
        verify_token = str(uuid.uuid4())
        kill_token = str(uuid.uuid4())
        
        # 2. These links will hit our FastAPI endpoints
        yes_link = f"{self.base_url}/api/auth/verify/{verify_token}?user_id={user_id}"
        no_link = f"{self.base_url}/api/auth/report_compromise/{kill_token}?user_id={user_id}"

        print("\n" + "="*50)
        print(f"EMAIL GENERATED FOR: {to_email}")
        print("Subject: ThreatSense Login Attempt Detected")
        print(f"CONFIRM: 'Yes, I'm In' Link: {yes_link}")
        print(f"REPORT: 'This is not me' Link: {no_link}")
        print("="*50 + "\n")

        # 3. Only send actual email if we have a real SendGrid key
        if self.client:
            message = Mail(
                from_email='threatsense25@gmail.com', # MUST be verified in SendGrid
                to_emails=to_email,
                subject=f'[SECURITY] ThreatSense Verification - {user_id}',
                plain_text_content=f'Verify your login for {user_id}: {yes_link} or report: {no_link}',
                html_content=f'''
                    <div style="font-family: sans-serif; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #eee;">
                        <h2 style="color: #d32f2f;">Critical: Identity Verification Needed</h2>
                        <p>A login was attempted for <b>{user_id}</b>.</p>
                        <p>If this was you, please click below to confirm:</p>
                        <a href="{yes_link}" style="display: inline-block; padding: 10px 20px; background: #2e7d32; color: #fff; text-decoration: none; border-radius: 4px;">✔ Yes, I'm In</a>
                        <p>If this was <b>NOT</b> you, click here immediately:</p>
                        <a href="{no_link}" style="display: inline-block; padding: 10px 20px; background: #c62828; color: #fff; text-decoration: none; border-radius: 4px;">✖ Not Me - Terminate Session</a>
                    </div>
                '''
            )
            try:
                response = self.client.send(message)
                if response.status_code >= 200 and response.status_code < 300:
                    print(f"SUCCESS: Email sent to {to_email} via SendGrid (Status: {response.status_code})")
                else:
                    print(f"ERROR: SendGrid accepted request but failed to deliver. Status: {response.status_code}")
                    print(f"Response Body: {response.body}")
            except Exception as e:
                print(f"FATAL ERROR: SendGrid failed for {to_email}. Error type: {type(e).__name__}")
                print(f"Details: {e}")
                print("HINT: Make sure 'threatsense25@gmail.com' is a VERIFIED SENDER in your SendGrid dashboard.")
        else:
            print(f"INFO: Email simulation mode active. Connect a SendGrid API key for real emails.")
        
        return {
            "verify_token": verify_token,
            "kill_token": kill_token
        }

# Create a singleton instance
email_service = EmailService()
