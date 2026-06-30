import os
import smtplib
from email.mime.text import MIMEText

# CrewFinder sends an email through your MMU Outlook (Office 365) account whenever
# a user receives a new message. Because MMU student mail runs on Outlook/Office 365,
# the recipient simply sees it as a normal email -> Outlook's own
# notification (desktop/mobile/web) fires automatically. No Graph API app
# registration is required for this approach.
#
# Required environment variables (see .env.example):
#   OUTLOOK_SENDER_EMAIL    - the Outlook/Office365 account CrewFinder sends FROM
#   OUTLOOK_SENDER_PASSWORD - an app password for that account
#   OUTLOOK_SMTP_HOST       - default: smtp.office365.com
#   OUTLOOK_SMTP_PORT       - default: 587

SMTP_HOST = os.environ.get("OUTLOOK_SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.environ.get("OUTLOOK_SMTP_PORT", "587"))
SENDER_EMAIL = os.environ.get("OUTLOOK_SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("OUTLOOK_SENDER_PASSWORD")


def send_new_message_email(to_email, sender_username, message_preview, app_url="http://localhost:5000"):
    """Send an email via Outlook SMTP so the recipient gets a normal Outlook
    notification that someone messaged them on CrewFinder. Fails silently
    (logs to console) if credentials aren't configured, so local dev without
    Outlook setup doesn't crash the app."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("[notifications] OUTLOOK_SENDER_EMAIL / OUTLOOK_SENDER_PASSWORD not set - skipping email.")
        return False

    preview = (message_preview[:140] + "...") if len(message_preview) > 140 else message_preview

    body = f"""Hi,

You have a new message on CrewFinder from {sender_username}:

"{preview}"

Reply here: {app_url}

— CrewFinder (MMU)
"""
    msg = MIMEText(body)
    msg["Subject"] = f"New CrewFinder message from {sender_username}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[notifications] Failed to send email: {e}")
        return False