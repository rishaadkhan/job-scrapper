"""Email Excel files"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime

def email_excel():
    """Email latest Excel file"""
    
    # Get credentials from environment
    email_to = os.environ.get('EMAIL_TO')
    email_from = os.environ.get('EMAIL_FROM')
    email_password = os.environ.get('EMAIL_PASSWORD')
    
    if not all([email_to, email_from, email_password]):
        print("Error: Missing email credentials")
        return
    
    # Find Excel file
    excel_files = [f for f in os.listdir('output') if f.endswith('.xlsx')]
    
    if not excel_files:
        print("No Excel files found")
        return
    
    excel_file = os.path.join('output', excel_files[0])
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = f"Job Leads - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Email body
    body = f"""
    Daily Job Scraper Results
    
    Date: {datetime.now().strftime('%Y-%m-%d')}
    File: {excel_files[0]}
    
    Please find attached the latest job leads.
    
    ---
    Automated Job Scraper
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach Excel file
    with open(excel_file, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={excel_files[0]}')
        msg.attach(part)
    
    # Send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_from, email_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✓ Emailed {excel_files[0]} to {email_to}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

if __name__ == '__main__':
    email_excel()
