import boto3
import json
import logging
from collections import defaultdict

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    sqs_client = boto3.client('sqs')
    lambda_client = boto3.client('lambda')

    queue_url = 'https://sqs.us-east-1.amazonaws.com/975050137696/cl-recipe-queue'

    user_files = defaultdict(list)
    messages_to_delete = []

    while True:
        # Receive messages from the SQS queue
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=10,
            VisibilityTimeout=30  # Ensures messages are not picked up again before processing
        )

        messages = response.get('Messages', [])
        if not messages:
            logger.info("No more messages in queue, exiting loop.")
            break

        # Process each message
        for message in messages:
            try:
                body = json.loads(message['Body'])
                logger.info(f"Processing message body: {body}")

                if 'Records' not in body:
                    logger.warning(f"Invalid message format, deleting message: {body}")
                    sqs_client.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    continue

                object_key = body['Records'][0]['s3']['object']['key']
                logger.info(f"Processing object key: {object_key}")
                
                parts = object_key.split('_')
                if len(parts) < 4:
                    logger.warning(f"Malformed key: {object_key}, skipping")
                    continue
                
                username, file_index, total_files, _ = parts
                file_index, total_files = int(file_index), int(total_files)

                user_files[username].append((file_index, object_key))
                messages_to_delete.append(message)

            except (KeyError, ValueError, IndexError) as e:
                logger.error(f"Error processing message: {e}")
                logger.error(f"Message body: {message['Body']}")
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )

        # Check if all files are present for each user
        for username, files in user_files.items():
            files.sort()
            expected_files = set(range(1, int(files[-1][1].split('_')[2]) + 1))
            actual_files = {file[0] for file in files}

        # Check if all files are from the same username
        all_files_belong_to_user = all(file[1].startswith(username) for file in files)

            logger.info(f"Expected files for user {username}: {expected_files}")
            logger.info(f"Actual files for user {username}: {actual_files}")

            if expected_files == actual_files and all_files_belong_to_user:
                object_names = [file[1] for file in files]
                try:
                    logger.info(f"Invoking cl-lambda-consolidator for user: {username}")
                    lambda_client.invoke(
                        FunctionName='cl-lambda-consolidator',
                        InvocationType='Event',
                        Payload=json.dumps({'username': username, 'object_names': object_names})
                    )
                    logger.info(f"Successfully invoked cl-lambda-consolidator for user: {username}")

                    # Remove processed messages
                    for message in messages_to_delete:
                        sqs_client.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )

                    # Reset lists after processing
                    user_files.pop(username, None)
                    messages_to_delete.clear()

                except Exception as e:
                    logger.error(f"Failed to invoke cl-lambda-consolidator: {e}")

    logger.info("Lambda function completed.")
