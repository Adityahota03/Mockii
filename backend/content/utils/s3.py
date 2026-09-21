import boto3
from django.conf import settings


def generate_study_material_url(
    object_key,
    expiration=300
):
    """
    Generates a short-lived presigned S3 URL for downloading a study material.
    """
    client_kwargs = {
        "service_name": "s3",
        "region_name": getattr(settings, "AWS_S3_REGION_NAME", "ap-south-1"),
    }

    access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)

    if access_key and secret_key:
        client_kwargs["aws_access_key_id"] = access_key
        client_kwargs["aws_secret_access_key"] = secret_key

    s3_client = boto3.client(**client_kwargs)

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""),
            "Key": object_key,
        },
        ExpiresIn=expiration,
    )

    return url
