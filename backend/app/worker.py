import asyncio
import random
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.email_subjects import default_subject
from app.models import Action, EmailAccount, Lead, Workspace
from app.services.emailer import needs_warmup, pick_account, send_email

settings = get_settings()


async def process_emails(db) -> int:
    """Envoie les emails dus via SMTP reel (si un compte est configure)."""
    now = datetime.now(timezone.utc)
    due = db.query(Action).filter(
        Action.status == "pending", Action.channel == "email", Action.scheduled_at <= now
    ).all()
    sent = 0
    for a in due:
        if not a.lead.email or a.lead.email_status not in ("valide", "risky"):
            a.status = "failed"
            continue
        account = await pick_account(db, a.lead.workspace_id)
        if not account:
            continue  # pas de SMTP configure -> reste en file (mode mock)
        limit = 5 if needs_warmup(account) else account.daily_limit
        used_today = db.query(Action).filter(
            Action.channel == "email", Action.sent_at >= now.replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        if used_today >= limit:
            continue  # quota anti-spam -> reporte
        ok = await send_email(account, a.lead.email, a.content, default_subject(a.lead.full_name))
        if ok:
            a.status = "sent"
            a.sent_at = now
            a.lead.crm_status = "contacted"
            sent += 1
        else:
            a.status = "failed"
        await asyncio.sleep(random.uniform(5, 15))  # anti-spam : gros delais entre emails
    return sent


async def process_linkedin_mock(db):
    """Simule les actions LinkedIn si aucune extension n'est connectee."""
    now = datetime.now(timezone.utc)
    due = db.query(Action).filter(
        Action.status == "pending", Action.channel.startswith("linkedin"), Action.scheduled_at <= now
    ).all()
    used = {}
    for a in due:
        ws = db.get(Workspace, a.lead.workspace_id)
        if used.get(ws.id, 0) >= min(ws.max_daily_linkedin_actions, settings.MAX_LINKEDIN_ACTIONS_PER_DAY):
            continue
        await asyncio.sleep(random.uniform(0.1, 0.3))
        a.status = "sent"
        a.sent_at = now
        a.lead.crm_status = "contacted"
        used[ws.id] = used.get(ws.id, 0) + 1


async def main():
    print("ProspAI worker demarre (tick 60 s)")
    while True:
        db = SessionLocal()
        try:
            n_email = await process_emails(db)
            await process_linkedin_mock(db)
            db.commit()
            if n_email:
                print(f"emails envoyes: {n_email}")
        except Exception as e:
            print("tick error:", e)
        finally:
            db.close()
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
