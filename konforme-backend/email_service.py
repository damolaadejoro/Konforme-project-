"""Email service supporting Resend and AWS SES providers."""

import html as html_module
import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

def _send_via_resend(to: str, subject: str, html_body: str) -> bool:
    """Send email via Resend API."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not configured — skipping email to %s", to)
        return False

    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.sender_email,
                "to": [to],
                "subject": subject,
                "html": html_body,
            },
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Email sent via Resend to %s: %s", to, subject)
        return True
    except Exception:
        logger.exception("Failed to send email via Resend to %s", to)
        return False


def _send_via_ses(to: str, subject: str, html_body: str) -> bool:
    """Send email via AWS SES."""
    import boto3
    from botocore.exceptions import ClientError

    kwargs = {
        "service_name": "ses",
        "region_name": settings.aws_ses_region,
    }
    if settings.aws_ses_access_key_id and settings.aws_ses_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_ses_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_ses_secret_access_key

    try:
        client = boto3.client(**kwargs)
        client.send_email(
            Source=settings.sender_email,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Html": {"Data": html_body, "Charset": "UTF-8"}},
            },
        )
        logger.info("Email sent via SES to %s: %s", to, subject)
        return True
    except ClientError:
        logger.exception("Failed to send email via SES to %s", to)
        return False


# ---------------------------------------------------------------------------
# Public send function
# ---------------------------------------------------------------------------

def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an email using the configured provider. Returns True on success."""
    if not settings.sender_email:
        logger.warning("SENDER_EMAIL not configured — skipping email to %s", to)
        return False

    if settings.email_provider == "ses":
        return _send_via_ses(to, subject, html_body)
    return _send_via_resend(to, subject, html_body)


# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

_STYLE = """
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f4f4f5; }
  .container { max-width: 560px; margin: 40px auto; background: #fff; border-radius: 8px; padding: 40px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .logo { font-size: 24px; font-weight: 700; color: #6366f1; margin-bottom: 24px; }
  h1 { font-size: 20px; color: #18181b; margin: 0 0 16px; }
  p { font-size: 15px; color: #3f3f46; line-height: 1.6; margin: 0 0 16px; }
  .btn { display: inline-block; background: #6366f1; color: #fff !important; text-decoration: none; padding: 12px 28px; border-radius: 6px; font-weight: 600; font-size: 15px; }
  .footer { text-align: center; font-size: 12px; color: #a1a1aa; margin-top: 32px; }
</style>
"""


def send_verification_email(email: str, token: str, base_url: str | None = None) -> bool:
    """Send email verification link."""
    url = base_url or settings.frontend_base_url
    verify_link = f"{url}/verify-email?token={token}"
    html = f"""<!DOCTYPE html><html><head>{_STYLE}</head><body>
    <div class="container">
      <div class="logo">Konforme</div>
      <h1>Verify your email address</h1>
      <p>Thanks for signing up! Please confirm your email address by clicking the button below.</p>
      <p><a class="btn" href="{verify_link}">Verify Email</a></p>
      <p>Or copy this link: <br><code>{verify_link}</code></p>
      <p class="footer">If you didn't create a Konforme account, you can safely ignore this email.</p>
    </div>
    </body></html>"""
    return send_email(email, "Verify your Konforme email", html)


def send_password_reset_email(email: str, token: str, base_url: str | None = None) -> bool:
    """Send password reset link."""
    url = base_url or settings.frontend_base_url
    reset_link = f"{url}/reset-password?token={token}"
    html = f"""<!DOCTYPE html><html><head>{_STYLE}</head><body>
    <div class="container">
      <div class="logo">Konforme</div>
      <h1>Reset your password</h1>
      <p>We received a request to reset your password. Click the button below to choose a new one. This link expires in 1 hour.</p>
      <p><a class="btn" href="{reset_link}">Reset Password</a></p>
      <p>Or copy this link: <br><code>{reset_link}</code></p>
      <p class="footer">If you didn't request a password reset, you can safely ignore this email.</p>
    </div>
    </body></html>"""
    return send_email(email, "Reset your Konforme password", html)


def send_invite_email(email: str, inviter_name: str, org_name: str, token: str, base_url: str | None = None) -> bool:
    """Send team invitation email."""
    esc = html_module.escape
    url = base_url or settings.frontend_base_url
    invite_link = f"{url}/accept-invite?token={token}"
    html = f"""<!DOCTYPE html><html><head>{_STYLE}</head><body>
    <div class="container">
      <div class="logo">Konforme</div>
      <h1>You've been invited to join {esc(org_name)}</h1>
      <p><strong>{esc(inviter_name)}</strong> has invited you to join <strong>{esc(org_name)}</strong> on Konforme, a NIS2 compliance platform.</p>
      <p><a class="btn" href="{invite_link}">Accept Invitation</a></p>
      <p>Or copy this link: <br><code>{invite_link}</code></p>
      <p class="footer">If you weren't expecting this invitation, you can safely ignore this email.</p>
    </div>
    </body></html>"""
    return send_email(email, f"Join {esc(org_name)} on Konforme", html)


def send_campaign_task_email(
    email: str,
    employee_name: str,
    task_description: str,
    completion_url: str,
    deadline: str | None = None,
) -> bool:
    """Send campaign task notification to an employee."""
    esc = html_module.escape
    deadline_line = f"<p><strong>Deadline:</strong> {esc(deadline)}</p>" if deadline else ""
    html = f"""<!DOCTYPE html><html><head>{_STYLE}</head><body>
    <div class="container">
      <div class="logo">Konforme</div>
      <h1>You have a new compliance task</h1>
      <p>Hi {esc(employee_name)},</p>
      <p>You've been assigned a compliance task:</p>
      <p><strong>{esc(task_description)}</strong></p>
      {deadline_line}
      <p><a class="btn" href="{esc(completion_url)}">Complete Task</a></p>
      <p>Or copy this link: <br><code>{esc(completion_url)}</code></p>
      <p class="footer">This is an automated message from Konforme NIS2 compliance platform.</p>
    </div>
    </body></html>"""
    return send_email(email, f"Compliance task: {esc(task_description)}", html)
