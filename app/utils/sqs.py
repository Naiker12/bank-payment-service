import boto3
import json
import os

sqs = boto3.client(
    "sqs",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)


def send_message(queue_url: str, body: dict) -> None:
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(body),
    )
