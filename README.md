# Serverless Signed URL File Gateway (Lab 4)

This repository contains the implementation of a secure, serverless file
gateway built on AWS. The solution allows clients to upload and download
files from a private Amazon S3 bucket using time-limited pre-signed URLs,
without exposing AWS credentials or making the bucket public.

---

## Architecture

**Core AWS Services**
- Amazon API Gateway (HTTP API)
- AWS Lambda (Python)
- Amazon S3 (private bucket)
- AWS IAM (least-privilege execution role)
- GitHub Actions (CI/CD with OIDC)

**High-level flow**
1. Client calls `POST /files` to request an upload URL.
2. API returns a pre-signed S3 PUT URL and an objectKey.
3. Client uploads the file directly to S3 using the signed URL.
4. Client calls `GET /files/{objectKey}` to download the file.
5. API returns an HTTP 302 redirect with a signed S3 GET URL.
6. Client follows the redirect and downloads the file from S3.

The API never handles file data directly, ensuring scalability and cost
efficiency.

---

## HTTP API

### POST /files — Generate upload URL

Generates a short-lived pre-signed Amazon S3 PUT URL.

**Request**
```json
{
  "filename": "hello.txt",
  "contentType": "text/plain"
}
```

**Response**
```json
{
  "objectKey": "uploads/<generated>_hello.txt",
  "uploadUrl": "https://<bucket>.s3.amazonaws.com/uploads/...?X-Amz-Signature=...",
  "expiresInSeconds": 900,
  "method": "PUT",
  "requiredHeaders": {
    "content-type": "text/plain"
  }
}
```

---

### GET /files/{objectKey} — Download file

Returns an HTTP redirect to a pre-signed S3 GET URL.

**Response**
- Status: `302 Found`
- Header:
  - `Location: <pre-signed S3 download URL>`

**Why HTTP 302?**

Using a redirect ensures that file downloads are handled directly by
Amazon S3, avoiding file proxying through API Gateway or Lambda and
improving scalability.

---

## Infrastructure as Code

Infrastructure is defined using **AWS SAM**.

Key resources:
- Private S3 bucket with public access blocked
- Lambda function to generate pre-signed URLs
- HTTP API routes for upload and download
- IAM role following least-privilege principles

---

## Application Code (Lambda)

The Lambda function is written in Python and uses `boto3` to generate
pre-signed URLs for S3 operations. The function never processes file
contents directly.

---

## Deployment Instructions (GitHub Actions + OIDC)

This project is deployed automatically using **GitHub Actions** with
**OIDC authentication**. No long-lived AWS credentials are stored in the
repository.

### Prerequisites
- An AWS account
- An IAM role configured for GitHub OIDC (with permission to deploy SAM/CloudFormation)
- GitHub repository variables:
  - `AWS_ACCOUNT_ID`
- AWS region configured in the workflow (e.g., `us-east-1`)

### Deployment Steps
1. Clone the repository:
```bash
git clone <your-repository-url>
cd <repository-folder>
```

2. Push changes to the main branch:
```bash
git add .
git commit -m "Deploy serverless file gateway"
git push origin main
```

3. GitHub Actions will automatically:
- Authenticate to AWS using OIDC
- Build the AWS SAM application
- Deploy or update the CloudFormation stack

4. Once the workflow completes successfully, retrieve the API Base URL
from the GitHub Actions output or CloudFormation stack outputs.

---

## Proof of Functionality (PowerShell)

```powershell
$env:API_BASE = "https://<api-id>.execute-api.<region>.amazonaws.com"
```

```powershell
$payload = @{ filename="hello.txt"; contentType="text/plain" } | ConvertTo-Json
$response = Invoke-RestMethod -Method POST -Uri "$env:API_BASE/files" -ContentType "application/json" -Body $payload
$uploadUrl = $response.uploadUrl
$objectKey = $response.objectKey
```

```powershell
"Hello from Lab 4" | Out-File -Encoding ascii hello.txt
curl.exe -i -X PUT "$uploadUrl" -H "Content-Type: text/plain" --upload-file hello.txt
```

```powershell
curl.exe -i "$env:API_BASE/files/$objectKey"
curl.exe -L "$env:API_BASE/files/$objectKey" -o downloaded_hello.txt
Get-Content .\downloaded_hello.txt
```

---

## Security Considerations

- S3 bucket blocks all public access.
- Clients never receive AWS credentials.
- Access is granted using time-limited pre-signed URLs.
- IAM permissions follow the principle of least privilege.
- Pre-signed URLs automatically expire.

---

## Cleanup

```bash
aws cloudformation delete-stack --stack-name <stack-name>
```

---

## Documentation Deliverable

A public Google Document accompanies this repository and includes:
- Architecture diagram
- API explanation
- Infrastructure as Code
- Application code
- Proof of functionality screenshots
