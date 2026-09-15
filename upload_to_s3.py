"""
AWS S3 Cloud Storage Uploader
Uploads the latest daily job leads spreadsheet to an Amazon S3 bucket.
Requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_BUCKET_NAME in environment.
"""
import os
import glob
from email_excel import get_latest_excel_file


def upload_to_s3(file_path: str = None):
    """Uploads the latest Excel report to AWS S3 and generates a secure pre-signed download URL."""
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("AWS_BUCKET_NAME")
    region_name = os.getenv("AWS_REGION", "ap-south-1")

    if not all([aws_access_key, aws_secret_key, bucket_name]):
        print("Notice: AWS credentials or AWS_BUCKET_NAME not set in environment. Skipping S3 upload.")
        return False

    try:
        import boto3
    except ImportError:
        print("Notice: boto3 is not installed. Install with 'pip install boto3' to enable AWS S3 upload.")
        return False

    target_file = file_path or get_latest_excel_file()
    if not target_file or not os.path.exists(target_file):
        print("Error: No Excel file found to upload.")
        return False

    filename = os.path.basename(target_file)
    s3_key = f"job-leads/{filename}"

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region_name
    )

    try:
        s3_client.upload_file(target_file, bucket_name, s3_key)
        
        # Generate pre-signed URL (valid for 7 days)
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": s3_key},
            ExpiresIn=604800  # 7 days
        )

        print(f"✓ Uploaded {filename} to S3 bucket '{bucket_name}'")
        print(f"  Key: {s3_key}")
        print(f"  Secure Download URL (valid 7 days): {presigned_url}")
        return presigned_url
    except Exception as e:
        print(f"Error uploading to AWS S3: {str(e)}")
        return False


if __name__ == "__main__":
    upload_to_s3()
