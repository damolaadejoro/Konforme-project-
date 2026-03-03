# Pre-Deployment Security Checklist

## Environment
- [ ] `.env` file is NOT committed to git
- [ ] `SECRET_KEY` is a strong random value (min 32 chars)
- [ ] `ALLOWED_ORIGINS` is set to production frontend URL only (no wildcards)
- [ ] `ENVIRONMENT` is set to `production`
- [ ] Database URL points to production database (not SQLite)

## API Security
- [ ] API keys are generated with `secrets.token_urlsafe(32)`
- [ ] API keys are stored as SHA-256 hashes only
- [ ] Rate limiting is configured appropriately
- [ ] CORS is restricted to known frontend origins
- [ ] All endpoints require API key authentication (except /health and /connect)

## AWS Security
- [ ] IAM role uses least-privilege read-only policy
- [ ] External ID is required for AssumeRole
- [ ] AWS credentials are never stored — only used transiently via STS
- [ ] Credentials are deleted from memory after session creation

## Headers
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] Strict-Transport-Security enabled
- [ ] Content-Security-Policy configured
- [ ] Cache-Control: no-store

## Data
- [ ] No PII stored beyond account names
- [ ] Audit log does not contain credentials or API keys
- [ ] Database backups are encrypted
- [ ] All Pydantic models use `extra="forbid"` for input validation

## Infrastructure
- [ ] HTTPS enforced (TLS 1.2+)
- [ ] Run `security_check.sh` with no critical findings
- [ ] Dependencies pinned to specific versions
- [ ] No debug mode in production
