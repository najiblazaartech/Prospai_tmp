"""Envoi email reel via SMTP (Gmail app-password / Brevo gratuit) + warm-up."""
import asyncio
from datetime import datetime, timedelta, timezone

import aiosmtplib
from email.message import EmailMessage
from sqlalchemy.orm import Session

from app.models import Action, EmailAccount, Lead


async def send_email(smtp: EmailAccount, to_email: str, content: str, subject: str) -> bool:
    """Envoie un email via le compte SMTP. Retourne True si OK."""
    msg = EmailMessage()
    msg["From"] = f"{smtp.sender_name or smtp.smtp_user} <{smtp.smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(content)
    try:
        await aiosmtplib.send(
            msg, hostname=smtp.smtp_host, port=smtp.smtp_port,
            username=smtp.smtp_user, password=smtp.smtp_password,
            starttls=True, timeout=30,
        )
        return True
    except Exception:
        return False


async def warmup_send(db: Session, account: EmailAccount) -> int:
    """Warm-up : 1 mail/jour vers une adresse de controle pendant 14 jours."""
    if account.warmup_until and account.warmup_until > datetime.now(timezone.utc):
        await send_email(account, account.smtp_user, "Warm-up ProspAI - test", "Warm-up")
        return 1
    return 0


def needs_warmup(account: EmailAccount) -> bool:
    if not account.warmup_until:
        return False
    return account.warmup_until > datetime.now(timezone.utc)


def start_warmup(account: EmailAccount, days: int = 14):
    """Demarre une periode de warm-up ; limite quotidienne progressive."""
    account.warmup_until = datetime.now(timezone.utc) + timedelta(days=days)
    account.daily_limit = 5  # monte progressivement jusqu'a 30 apres le warm-up


async def pick_account(db: Session, workspace_id: int) -> EmailAccount | None:
    return (
        db.query(EmailAccount)
        .filter(EmailAccount.workspace_id == workspace_id, EmailAccount.is_active == True)  # noqa: E712
        .first()
    )
