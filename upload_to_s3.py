"""Upload Excel files to AWS S3"""
import os
import boto3
from datetime import datetime

def upload_to_s3():
    """Upload latest Excel file to S3"""
    
    # Get AWS credentials from environment
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.environ.get('AWS_BUCKET_NAME')
    
    if not all([aws_access_key, aws_secret_key, bucket_name]):
        print("Error: Missing AWS credentials")
        return
    
    # Find Excel file
    excel_files = [f for f in os.listdir('output') if f.endswith('.xlsx')]
    
    if not excel_files:
        print("No Excel files found")
        return
    
    excel_file = os.path.join('output', excel_files[0])
    
    # Upload to S3
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    
    s3_key = f"job-leads/{excel_files[0]}"
    
    try:
        s3_client.upload_file(excel_file, bucket_name, s3_key)
        
        # Generate pre-signed URL (valid for 7 days)
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=604800  # 7 days
        )
        
        print(f"✓ Uploaded {excel_files[0]} to S3")
        print(f"  Bucket: {bucket_name}")
        print(f"  Key: {s3_key}")
        print(f"  Download URL (7 days): {url}")
        
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")

if __name__ == '__main__':
    upload_to_s3()
