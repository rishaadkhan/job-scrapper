"""
Google Drive Cloud Storage Uploader
Uploads the latest daily job leads spreadsheet to Google Drive.
Requires GDRIVE_CREDENTIALS (JSON string) and GDRIVE_FOLDER_ID environment variables.
"""
import os
import glob
from email_excel import get_latest_excel_file


def upload_to_gdrive(file_path: str = None):
    """Uploads the latest Excel report to Google Drive."""
    creds_json = os.getenv("GDRIVE_CREDENTIALS")
    folder_id = os.getenv("GDRIVE_FOLDER_ID")

    if not creds_json or not folder_id:
        print("Notice: GDRIVE_CREDENTIALS or GDRIVE_FOLDER_ID not set in environment. Skipping Google Drive upload.")
        return False

    try:
        from pydrive2.auth import GoogleAuth
        from pydrive2.drive import GoogleDrive
    except ImportError:
        print("Notice: pydrive2 is not installed. Install with 'pip install pydrive2' to enable Google Drive upload.")
        return False

    target_file = file_path or get_latest_excel_file()
    if not target_file or not os.path.exists(target_file):
        print("Error: No Excel file found to upload.")
        return False

    filename = os.path.basename(target_file)
    tmp_creds_path = "gdrive_credentials_temp.json"

    try:
        with open(tmp_creds_path, "w", encoding="utf-8") as f:
            f.write(creds_json)

        gauth = GoogleAuth()
        gauth.LoadCredentialsFile(tmp_creds_path)
        drive = GoogleDrive(gauth)

        file_drive = drive.CreateFile({
            "title": filename,
            "parents": [{"id": folder_id}]
        })
        file_drive.SetContentFile(target_file)
        file_drive.Upload()

        print(f"✓ Uploaded {filename} to Google Drive")
        print(f"  File ID: {file_drive['id']}")
        print(f"  View: https://drive.google.com/file/d/{file_drive['id']}/view")
        return True
    except Exception as e:
        print(f"Error uploading to Google Drive: {str(e)}")
        return False
    finally:
        if os.path.exists(tmp_creds_path):
            os.remove(tmp_creds_path)


if __name__ == "__main__":
    upload_to_gdrive()
