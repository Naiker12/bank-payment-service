import boto3
import os
from datetime import datetime

s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

BUCKET = os.getenv("CATALOG_BUCKET", "")


def upload_csv(csv_content: str) -> str:
    key = f"catalogs/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=csv_content.encode("utf-8"),
        ContentType="text/csv",
    )
    return key
