import os
import smtplib
import uuid
from email.message import EmailMessage
from core.config import settings


class EmailService:
    def __init__(self):
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = settings.SMTP_EMAIL
        self.app_password = settings.SMTP_APP_PASSWORD
        self.base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    def send_verification_email(self, to_email: str, user_id: str):
        """Generates UUID tokens and sends the Yes/No verification email via Gmail SMTP."""

        # 1. Generate unique security tokens
        verify_token = str(uuid.uuid4())
        kill_token = str(uuid.uuid4())

        # 2. Build magic links
        yes_link = f"{self.base_url}/api/auth/verify/{verify_token}?user_id={user_id}"
        no_link = f"{self.base_url}/api/auth/report_compromise/{kill_token}?user_id={user_id}"

        print("\n" + "="*50)
        print(f"EMAIL GENERATED FOR: {to_email}")
        print("Subject: ThreatSense Login Attempt Detected")
        print(f"CONFIRM: 'Yes, I'm In' Link: {yes_link}")
        print(f"REPORT: 'This is not me' Link: {no_link}")
        print("="*50 + "\n")

        # 3. Build the EmailMessage
        msg = EmailMessage()
        msg["Subject"] = f"[SECURITY] ThreatSense Verification - {user_id}"
        msg["From"] = self.sender_email
        msg["To"] = to_email
        msg.set_content(
            f"Verify your login for {user_id}: {yes_link}\nOr report compromise: {no_link}"
        )
        msg.add_alternative(f'''
            <div style="font-family: sans-serif; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #eee;">
                <h2 style="color: #d32f2f;">Critical: Identity Verification Needed</h2>
                <p>A login was attempted for <b>{user_id}</b>.</p>
                <p>If this was you, please click below to confirm:</p>
                <a href="{yes_link}" style="display: inline-block; padding: 10px 20px; background: #2e7d32; color: #fff; text-decoration: none; border-radius: 4px;">✔ Yes, I'm In</a>
                <p>If this was <b>NOT</b> you, click here immediately:</p>
                <a href="{no_link}" style="display: inline-block; padding: 10px 20px; background: #c62828; color: #fff; text-decoration: none; border-radius: 4px;">✖ Not Me - Terminate Session</a>
            </div>
        ''', subtype="html")

        # 4. Send via Gmail SMTP with STARTTLS on port 587
        if "placeholder" in self.sender_email or "placeholder" in self.app_password:
            print("INFO: Email simulation mode active. Set SMTP_EMAIL and SMTP_APP_PASSWORD in .env for real emails.")
        else:
            try:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.ehlo()
                    server.starttls()        # Upgrade to secure TLS connection
                    server.ehlo()
                    server.login(self.sender_email, self.app_password)
                    server.send_message(msg)
                print(f"SUCCESS: Email sent to {to_email} via Gmail SMTP.")
            except smtplib.SMTPAuthenticationError:
                print("FATAL: Gmail authentication failed. Make sure you are using a Gmail App Password, not your regular password.")
                print("Generate one at: https://myaccount.google.com/apppasswords")
            except Exception as e:
                print(f"FATAL ERROR: Could not send email. Error: {type(e).__name__}: {e}")

        return {
            "verify_token": verify_token,
            "kill_token": kill_token
        }


# Singleton instance
email_service = EmailService()
