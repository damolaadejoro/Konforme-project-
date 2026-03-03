# Connecting Your AWS Account to Konforme

## Prerequisites
- AWS account with IAM admin access
- Konforme backend running

## Step 1: Create an IAM Policy

1. Open the AWS IAM Console
2. Go to **Policies** > **Create Policy**
3. Click **JSON** tab and paste the contents of `iam_policy.json` from this repository
4. Name the policy `KonformeReadOnlyPolicy`
5. Click **Create Policy**

## Step 2: Create an IAM Role

1. Go to **Roles** > **Create Role**
2. Select **Another AWS account** as the trusted entity
3. Enter the Konforme AWS Account ID (provided by your Konforme admin)
4. Check **Require external ID** and enter a unique external ID (e.g., a UUID)
5. Click **Next** and attach the `KonformeReadOnlyPolicy`
6. Name the role `KonformeAuditRole`
7. Click **Create Role**

## Step 3: Note the Role ARN

After creating the role, copy the **Role ARN** from the role summary page. It will look like:

```
arn:aws:iam::123456789012:role/KonformeAuditRole
```

## Step 4: Connect via Konforme API

```bash
curl -X POST https://your-konforme-api.com/api/v1/connect \
  -H "Content-Type: application/json" \
  -d '{
    "account_name": "My AWS Account",
    "role_arn": "arn:aws:iam::123456789012:role/KonformeAuditRole",
    "external_id": "your-external-id-here"
  }'
```

The response will include your **API key** (shown only once — save it securely):

```json
{
  "account_id": "uuid-here",
  "account_name": "My AWS Account",
  "aws_account_id": "123456789012",
  "api_key": "your-api-key-here"
}
```

## Step 5: Run Your First Scan

```bash
curl -X POST https://your-konforme-api.com/api/v1/scan/{account_id} \
  -H "X-API-Key: your-api-key-here"
```

## Trust Policy Reference

The IAM role's trust policy should look like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::KONFORME_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "your-external-id-here"
        }
      }
    }
  ]
}
```
