"""Moteur de sequences : planification avec quotas et jitter anti-ban."""
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Action, Campaign, Lead


def enqueue_campaign_for_lead(db: Session, lead: Lead, campaign: Campaign) -> list:
    """Cree les actions en file pour un lead (mode revue manuelle respecte)."""
    actions = []
    now = datetime.now(timezone.utc)
    for step in campaign.steps:
        if step.day_offset == 0:
            # Premiere action : due immediatement (apres validation RGPD).
            # Le jitter humain est applique a l'execution (worker/extension), pas ici.
            scheduled = now
            status = "review" if (lead.workspace and lead.workspace.manual_review) else "pending"
        else:
            scheduled = now + timedelta(days=step.day_offset, minutes=random.randint(0, 600))
            status = "pending"
        a = Action(
            lead_id=lead.id,
            step_id=step.id,
            channel=step.channel,
            kind=_kind_for(step.channel),
            status=status,
            scheduled_at=scheduled,
            content=render_template(step.template, lead),
        )
        db.add(a)
        actions.append(a)
    db.commit()
    return actions


def _kind_for(channel: str) -> str:
    return {
        "linkedin_invitation": "invitation",
        "linkedin_message": "message",
        "email": "email",
    }.get(channel, channel)


def render_template(template: str, lead: Lead) -> str:
    """Rendu simple ; remplace par generation LLM si cle Mistral fournie."""
    return (template or "Bonjour {{prenom}}...").replace(
        "{{prenom}}", lead.full_name.split(" ")[0]
    ).replace(
        "{{entreprise}}", lead.company
    ).replace(
        "{{role}}", lead.role
    )


def daily_actions_used(db: Session, workspace_id: int) -> int:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(Action)
        .join(Lead)
        .filter(Lead.workspace_id == workspace_id, Action.sent_at >= today)
        .count()
    )
