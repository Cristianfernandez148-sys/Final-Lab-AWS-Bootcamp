import json
import os
import time
import uuid
import urllib.parse
import boto3

s3 = boto3.client("s3")


def lambda_handler(event, context):
    bucket = os.environ["BUCKET_NAME"]
    upload_exp = int(os.environ.get("UPLOAD_EXPIRES_SECONDS", "900"))      # 15 min
    download_exp = int(os.environ.get("DOWNLOAD_EXPIRES_SECONDS", "3600")) # 1 hour

    method = event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("rawPath", "")

    # POST /files
    # Returns a pre-signed PUT URL for direct upload to S3

    if method == "POST" and path == "/files":
        body = json.loads(event.get("body") or "{}")

        filename = body.get("filename", "file")
        content_type = body.get("contentType")  # e.g. "text/plain"

        # Generate unique object key
        object_key = f"uploads/{int(time.time())}_{uuid.uuid4().hex}_{filename}"

        # Parameters to be signed
        params = {
            "Bucket": bucket,
            "Key": object_key,
        }

        # IMPORTANT: If Content-Type is provided, it MUST be signed
        if content_type:
            params["ContentType"] = content_type

        upload_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=upload_exp,
        )

        return {
            "statusCode": 200,
            "headers": {
                "content-type": "application/json"
            },
            "body": json.dumps({
                "objectKey": object_key,
                "uploadUrl": upload_url,
                "expiresInSeconds": upload_exp,
                "method": "PUT",
                "requiredHeaders": {
                    "content-type": content_type
                } if content_type else {}
            }),
        }
    # GET /files/{objectKey}
    # Returns an HTTP 302 redirect to a pre-signed GET URL
    if method == "GET" and path.startswith("/files/"):
        # Extract object key from path
        object_key = path[len("/files/"):]
        object_key = urllib.parse.unquote(object_key)

        if not object_key:
            return {
                "statusCode": 400,
                "headers": {"content-type": "application/json"},
                "body": json.dumps({"error": "objectKey is required"}),
            }

        download_url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket,
                "Key": object_key,
            },
            ExpiresIn=download_exp,
        )
        # HTTP redirect (required by the lab)
        return {
            "statusCode": 302,
            "headers": {
                "Location": download_url
            },
            "body": "",
        }

    # Fallback
    return {
        "statusCode": 404,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({"error": "Not Found"}),
    }