import datetime
import json
import base64
import boto3
import rsa
from botocore.exceptions import ClientError

# TODO: add this to SSM Parameter Store 
CLOUDFRONT_URL = "https://d20ii5cyt7sb3r.cloudfront.net/"

# TODO: add this to SSM Parameter Store
KEY_PAIR_ID = "KHPQZC3AZEI32"

def get_secret(secret_name, region_name="us-east-1"):
    """
    Retrieve a secret from AWS Secrets Manager.
    """
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        # Retrieve the secret value from AWS Secrets Manager
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e

    # Return the secret string (assuming it's in PEM format)
    return get_secret_value_response['SecretString']

# Query the DB for available recipes

def get_recipe_from_dynamodb(username, region_name="us-east-1"):
    """
    Retrieve the recipe field from DynamoDB for the given username.
    """
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table('cl-client-database')

    try:
        response = table.get_item(Key={'username': username})
        # Check if the item exists and has the 'recipe' field
        if 'Item' in response and 'recipe' in response['Item']:
            return response['Item']['recipe']
        else:
            raise ValueError("Recipe not found for the specified user.")
    except ClientError as e:
        raise e

# TODO: decode JWT for username
username = "testuser"
OBJECT_NAME = get_recipe_from_dynamodb(username)


# Expiration time for the signed URL (5 hours from now)
UTC_TIMEZONE = datetime.timezone.utc
EXPIRE_TIME = int((datetime.datetime.now(UTC_TIMEZONE) + datetime.timedelta(hours=5)).timestamp())

# Create the policy
policy = {
    "Statement": [
        {
            "Resource": "*",
            "Condition": {
                "DateLessThan": {"AWS:EpochTime": EXPIRE_TIME}
            }
        }
    ]
}

# Convert policy to JSON and base64 encode it
policy_json = json.dumps(policy, separators=(",", ":"))
policy_b64 = base64.b64encode(policy_json.encode()).decode()

# Retrieve the private key from Secrets Manager
private_key_pem = get_secret("cl-private-key-distribution") 
private_key = rsa.PrivateKey.load_pkcs1(private_key_pem.encode())

# Sign the policy with the private key
signature = rsa.sign(policy_json.encode(), private_key, "SHA-1")
signature_b64 = base64.b64encode(signature).decode()

# Generate the signed URL
signed_url = f"{CLOUDFRONT_URL}{OBJECT_NAME}?Policy={policy_b64}&Signature={signature_b64}&Key-Pair-Id={KEY_PAIR_ID}"

def lambda_handler(event, context):
    print("Generated Signed URL:")
    print(signed_url)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            # CORS headers are handled by API Gateway
        },
        'body': json.dumps({
            'url': signed_url
        })
    }
