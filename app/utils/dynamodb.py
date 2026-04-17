import boto3
import os

# No load_dotenv() as requested by user

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

table = dynamodb.Table(os.getenv("PAYMENT_TABLE", "payment"))
