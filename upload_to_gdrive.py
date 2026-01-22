"""Upload Excel files to Google Drive"""
import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def upload_to_gdrive():
    """Upload latest Excel file to Google Drive"""
    
    # Get credentials from environment
    creds_json = os.environ.get('GDRIVE_CREDENTIALS')
    folder_id = os.environ.get('GDRIVE_FOLDER_ID')
    
    if not creds_json or not folder_id:
        print("Error: Missing GDRIVE_CREDENTIALS or GDRIVE_FOLDER_ID")
        return
    
    # Save credentials to file
    with open('credentials.json', 'w') as f:
        f.write(creds_json)
    
    # Authenticate
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile('credentials.json')
    drive = GoogleDrive(gauth)
    
    # Find Excel file
    excel_files = [f for f in os.listdir('output') if f.endswith('.xlsx')]
    
    if not excel_files:
        print("No Excel files found")
        return
    
    excel_file = os.path.join('output', excel_files[0])
    
    # Upload to Google Drive
    file_drive = drive.CreateFile({
        'title': excel_files[0],
        'parents': [{'id': folder_id}]
    })
    file_drive.SetContentFile(excel_file)
    file_drive.Upload()
    
    print(f"✓ Uploaded {excel_files[0]} to Google Drive")
    print(f"  File ID: {file_drive['id']}")
    print(f"  View: https://drive.google.com/file/d/{file_drive['id']}/view")

if __name__ == '__main__':
    upload_to_gdrive()
