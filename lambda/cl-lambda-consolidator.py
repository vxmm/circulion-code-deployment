import boto3
import zipfile
import logging

logger = logging.getLogger()

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    username = event['username']
    object_names = event['object_names']
    logger.info(f"Received event: {event}")
    source_bucket = 'cl-recipe-bucket-v1'
    destination_bucket = 'cl-recipe-distribution'

    # Create a zip file in the /tmp directory
    zip_file_path = f'/tmp/{username}_bundle.zip'

    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for object_name in object_names:
            # Retrieve the object from S3
            response = s3_client.get_object(Bucket=source_bucket, Key=object_name)
            logger.info(f"Retrieved object: {object_name}")
            object_data = response['Body'].read()

            # Write the object data to the zip file
            zipf.writestr(object_name, object_data)

    # Upload the zip file to the destination bucket
    zip_file_key = f'{username}_bundle.zip'
    s3_client.upload_file(zip_file_path, destination_bucket, zip_file_key)

    print(f"Uploaded zip file to s3://{destination_bucket}/{zip_file_key}")