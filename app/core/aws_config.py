import boto3
from app.core.config import settings

aws_access_key_id = settings.AWS_ACCESS_KEY_ID
aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY

aws_bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=settings.AWS_REGION,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)


