"""
Excel Email Dispatcher
Emails the latest daily job leads spreadsheet to configured recipients via SMTP.
Integrates with environment variables configured in .env.
"""
import os
import glob
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime


def get_latest_excel_file(output_dir: str = "output") -> str:
    """Finds the most recently created or modified Excel file in output directory."""
    if not os.path.exists(output_dir):
        return ""
    files = glob.glob(os.path.join(output_dir, "*.xlsx"))
    if not files:
        return ""
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def email_excel(recipient: str = None, file_path: str = None):
    """Sends latest Excel report via SMTP email."""
    # Load configuration from environment
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    sender_email = os.getenv("SMTP_FROM", smtp_user)
    email_to = recipient or os.getenv("DIGEST_EMAIL_TO") or os.getenv("EMAIL_TO")

    if not email_to:
        print("Error: Recipient email address not specified (set DIGEST_EMAIL_TO or EMAIL_TO in .env).")
        return False

    if not smtp_user or not smtp_password:
        print("Error: Missing SMTP credentials in environment (set SMTP_USER and SMTP_PASSWORD in .env).")
        return False

    target_file = file_path or get_latest_excel_file()
    if not target_file or not os.path.exists(target_file):
        print(f"Error: No valid Excel file found to email in output directory.")
        return False

    filename = os.path.basename(target_file)
    today_str = datetime.now().strftime("%Y-%m-%d")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email_to
    msg["Subject"] = f"🎯 High-Conversion Job Leads — {today_str}"

    body = f"""Hello,

Attached is your daily qualified backend job leads spreadsheet for {today_str}.

Spreadsheet Details:
- File: {filename}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

All listings have been filtered for India backend engineering roles (0-3 years) and scored against your resume.

Best regards,
Enterprise Job Scraper Engine
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        with open(target_file, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)

        server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()

        print(f"✓ Successfully sent {filename} to {email_to}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


if __name__ == "__main__":
    email_excel()
