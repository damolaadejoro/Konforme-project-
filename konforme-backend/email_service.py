"""Email service supporting Resend and AWS SES providers."""

import html as html_module
import logging

import httpx

from config import settings
from email_translations import get_email_text

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


def send_verification_email(email: str, token: str, base_url: str | None = None, lang: str = "en") -> bool:
    """Send email verification link."""
    t = lambda key, **kw: get_email_text(lang, key, **kw)
    url = base_url or settings.frontend_base_url
    verify_link = f"{url}/verify-email?token={token}"
    html = f"""<!DOCTYPE html><html><head>{_STYLE}</head><body>
    <div class="container">
      <div class="logo">Konforme</div>
      <h1>{t("verify_heading")}</h1>
      <p>{t("verify_body")}</p>
      <p><a class="btn" href="{verify_link}">{t("verify_button")}</a></p>
      <p>{t("copy_link")} <br><code>{verify_link}</code></p>
      <p class="footer">{t("verify_footer")}</p>
    </div>
    </body></html>"""
    return send_email(email, t("verify_subject"), html)


def send_password_reset_email(email: str, token: str, base_url: str | None = None, lang: str = "en") -> bool:
    """Send password reset link."""
    t = lambda key, **kw: get_email_text(lang, key, **kw)
    url = base_url or settings.frontend_base_url
    reset_link = f"{url}/reset-password?token={token}"
    html = f"""<!DOCTYPE html><html><head>{_STYLE}</head><body>
    <div class="container">
      <div class="logo">Konforme</div>
      <h1>{t("reset_heading")}</h1>
      <p>{t("reset_body")}</p>
      <p><a class="btn" href="{reset_link}">{t("reset_button")}</a></p>
      <p>{t("copy_link")} <br><code>{reset_link}</code></p>
      <p class="footer">{t("reset_footer")}</p>
    </div>
    </body></html>"""
    return send_email(email, t("reset_subject"), html)


def send_invite_email(email: str, inviter_name: str, org_name: str, token: str, base_url: str | None = None, lang: str = "en") -> bool:
    """Send team invitation email."""
    esc = html_module.escape
    t = lambda key, **kw: get_email_text(lang, key, **kw)
    url = base_url or settings.frontend_base_url
    invite_link = f"{url}/accept-invite?token={token}"
    html = f"""<!DOCTYPE html><html><head>{_STYLE}</head><body>
    <div class="container">
      <div class="logo">Konforme</div>
      <h1>{t("invite_heading", org_name=esc(org_name))}</h1>
      <p>{t("invite_body", inviter_name=esc(inviter_name), org_name=esc(org_name))}</p>
      <p><a class="btn" href="{invite_link}">{t("invite_button")}</a></p>
      <p>{t("copy_link")} <br><code>{invite_link}</code></p>
      <p class="footer">{t("invite_footer")}</p>
    </div>
    </body></html>"""
    return send_email(email, t("invite_subject", org_name=esc(org_name)), html)


def send_campaign_task_email(
    email: str,
    employee_name: str,
    task_description: str,
    completion_url: str,
    deadline: str | None = None,
    lang: str = "en",
) -> bool:
    """Send campaign task notification to an employee."""
    esc = html_module.escape
    t = lambda key, **kw: get_email_text(lang, key, **kw)
    deadline_line = f"<p><strong>{t('task_deadline')}</strong> {esc(deadline)}</p>" if deadline else ""
    html = f"""<!DOCTYPE html><html><head>{_STYLE}</head><body>
    <div class="container">
      <div class="logo">Konforme</div>
      <h1>{t("task_heading")}</h1>
      <p>{t("task_greeting", employee_name=esc(employee_name))}</p>
      <p>{t("task_body")}</p>
      <p><strong>{esc(task_description)}</strong></p>
      {deadline_line}
      <p><a class="btn" href="{esc(completion_url)}">{t("task_button")}</a></p>
      <p>{t("copy_link")} <br><code>{esc(completion_url)}</code></p>
      <p class="footer">{t("task_footer")}</p>
    </div>
    </body></html>"""
    return send_email(email, t("task_subject", task_description=esc(task_description)), html)


def send_remediation_reminder(
    email: str,
    task_title: str,
    due_date: str,
    task_url: str,
    lang: str = "en",
) -> bool:
    """Send overdue remediation task reminder."""
    esc = html_module.escape
    t = lambda key, **kw: get_email_text(lang, key, **kw)
    html = f"""<!DOCTYPE html><html><head>{_STYLE}</head><body>
    <div class="container">
      <div class="logo">Konforme</div>
      <h1>{t("reminder_heading")}</h1>
      <p>{t("reminder_body", task_title=esc(task_title), due_date=esc(due_date))}</p>
      <p><a class="btn" href="{esc(task_url)}">{t("reminder_button")}</a></p>
      <p class="footer">{t("reminder_footer")}</p>
    </div>
    </body></html>"""
    return send_email(email, t("reminder_subject", task_title=esc(task_title)), html)


def send_escalation_notification(
    email: str,
    task_title: str,
    reschedule_count: int,
    lang: str = "en",
) -> bool:
    """Send chronic slip escalation notification."""
    esc = html_module.escape
    t = lambda key, **kw: get_email_text(lang, key, **kw)
    html = f"""<!DOCTYPE html><html><head>{_STYLE}</head><body>
    <div class="container">
      <div class="logo">Konforme</div>
      <h1>{t("escalation_heading")}</h1>
      <p>{t("escalation_body", task_title=esc(task_title), reschedule_count=str(reschedule_count))}</p>
      <p class="footer">{t("escalation_footer")}</p>
    </div>
    </body></html>"""
    return send_email(email, t("escalation_subject", task_title=esc(task_title)), html)
