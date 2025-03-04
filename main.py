import boto3
import os
import hashlib
import csv
from datetime import datetime
from io import StringIO

def assume_role(role_arn, session_name):
    sts_client = boto3.client('sts')
    assumed_role = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
    return assumed_role['Credentials']

def calculate_md5(file_name):
    return hashlib.md5(file_name.encode()).hexdigest()

def get_aws_username():
    iam_client = boto3.client('iam')
    user = iam_client.get_user()
    return user['User']['UserName']

def log_to_s3(bucket_name, log_entry, credentials):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    current_date = datetime.now().strftime("%d_%m_%Y")
    log_file_key = f"{current_date}_logs.csv"

    log_csv = StringIO()
    csv_writer = csv.writer(log_csv)

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=log_file_key)
        existing_content = response['Body'].read().decode('utf-8')
        log_csv.write(existing_content)
    except s3_client.exceptions.NoSuchKey:
        csv_writer.writerow(["Operation", "User", "Timestamp", "Description"])

    csv_writer.writerow(log_entry)
    log_csv.seek(0)

    s3_client.put_object(Bucket=bucket_name, Key=log_file_key, Body=log_csv.getvalue(), ContentType='text/csv')

def validate_txt_files(local_path):
    """Filters and returns only .txt files from the given directory."""
    return [f for f in os.listdir(local_path) if f.endswith('.txt') and os.path.isfile(os.path.join(local_path, f))]

def upload_files_to_s3(local_path, bucket_name, credentials, log_bucket_name):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    aws_username = get_aws_username()

    # Validate and filter only .txt files
    txt_files = validate_txt_files(local_path)
    total_files = len(txt_files)

    if total_files == 0:
        print("No .txt files found. No files uploaded.")
        return

    for file_index, file in enumerate(txt_files, start=1):
        file_path = os.path.join(local_path, file)
        md5_hash = calculate_md5(file)
        new_file_name = f"{aws_username}_{file_index}_{total_files}_{md5_hash}"

        s3_key = new_file_name
        s3_client.upload_file(file_path, bucket_name, s3_key)
        print(f'Uploaded {file_path} to s3://{bucket_name}/{s3_key}')

        timestamp = datetime.now().strftime("%d-%m-%YT%H:%M:%S")
        log_entry = ["UPLOAD", aws_username, timestamp, f"File {file} was uploaded as {new_file_name}."]
        log_to_s3(log_bucket_name, log_entry, credentials)

def main():
    role_arn = "arn:aws:iam::975050137696:role/cl-allow-recipe-upload-role"
    bucket_name = "cl-recipe-bucket-v1"
    log_bucket_name = "cl-recipe-logs"
    session_name = "TestSession"
    local_path = "/Users/vxmm/Desktop/circulion/testFolder"

    credentials = assume_role(role_arn, session_name)
    upload_files_to_s3(local_path, bucket_name, credentials, log_bucket_name)

if __name__ == "__main__":
    main()