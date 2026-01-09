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

---

## Deployment Instructions (GitHub Actions + OIDC)

This project is deployed automatically using **GitHub Actions** with
**OpenID Connect (OIDC)**. No long-lived AWS access keys are stored in the
repository.

### Prerequisites

- An AWS account
- An AWS IAM Role for GitHub Actions named **githubconnect**
- GitHub repository variables:
  - `AWS_ACCOUNT_ID` — AWS account number
  - `AWS_REGION` — AWS region where the stack will be deployed (e.g. `us-east-1`)
- GitHub Actions enabled on the repository

### AWS Region Configuration

The deployment workflow (`deploy.yaml`) uses the `AWS_REGION` repository
variable to define the target AWS region. All AWS resources (API Gateway,
Lambda, and S3) are created in this region.

Example usage inside the workflow:
```yaml
- name: Configure AWS credentials via OIDC
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::${{ vars.AWS_ACCOUNT_ID }}:role/githubconnect
    aws-region: ${{ vars.AWS_REGION }}
```

### IAM Role (githubconnect)

The IAM role **githubconnect** is required for GitHub Actions to deploy
infrastructure using OIDC.

Role ARN format:
```
arn:aws:iam::<AWS_ACCOUNT_ID>:role/githubconnect
```

The role must:
- Trust GitHub as an OIDC federated identity provider
- Allow `sts:AssumeRoleWithWebIdentity`
- Grant permissions to deploy CloudFormation/SAM stacks and related AWS resources

Example trust policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<ORG>/<REPO>:*"
        }
      }
    }
  ]
}
```

### Deployment Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-folder>
```

2. Push changes to the main branch:
```bash
git add .
git commit -m "Deploy serverless file gateway"
git push origin main
```

3. GitHub Actions workflow (`deploy.yaml`) will:
- Authenticate to AWS using OIDC and the `githubconnect` role
- Use the `AWS_REGION` variable to select the deployment region
- Build the AWS SAM application
- Deploy or update the CloudFormation stack

4. After a successful run, retrieve the **API Base URL** from:
- GitHub Actions job output, or
- CloudFormation stack outputs (`ApiBaseUrl`)

---

## Proof of Functionality (PowerShell)

```powershell
$env:API_BASE = "https://<api-id>.execute-api.<AWS_REGION>.amazonaws.com"
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
