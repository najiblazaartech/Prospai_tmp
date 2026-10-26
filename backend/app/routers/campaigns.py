from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Action, Campaign, Lead, SequenceStep, User, WorkspaceMember
from app.schemas import CampaignCreate
from app.services.sequence_engine import enqueue_campaign_for_lead

router = APIRouter(prefix="/campaigns", tags=["campagnes & sequences"])


def _ws_id(db: Session, user: User) -> int:
    m = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).first()
    if not m:
        raise HTTPException(404, "Aucun workspace")
    return m.workspace_id


@router.get("")
def list_campaigns(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws_id = _ws_id(db, user)
    out = []
    for c in db.query(Campaign).filter(Campaign.workspace_id == ws_id).all():
        leads = db.query(Lead).filter(Lead.campaign_id == c.id).count()
        actions = db.query(Action).join(Lead).filter(Lead.campaign_id == c.id).all()
        sent = sum(1 for a in actions if a.sent_at)
        replies = sum(1 for a in actions if a.status == "replied")
        out.append({
            "id": c.id, "name": c.name, "status": c.status, "prompt": c.prompt,
            "leads": leads, "sent": sent, "replies": replies,
            "reply_rate": round(replies / sent * 100, 1) if sent else 0,
        })
    return out


@router.post("")
def create_campaign(body: CampaignCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws_id = _ws_id(db, user)
    c = Campaign(workspace_id=ws_id, name=body.name, prompt=body.prompt)
    db.add(c)
    db.flush()
    defaults = [
        (0, "linkedin_invitation", "always",
         "Bonjour {{prenom}}, je suis tombe sur {{entreprise}} et votre approche m'interesse beaucoup. Au plaisir de connecter !"),
        (3, "linkedin_message", "no_reply",
         "Bonjour {{prenom}}, savez-vous si la prospection est un sujet chez {{entreprise}} ?"),
        (5, "email", "not_accepted",
         "Bonjour {{prenom}}, je vous ecris au sujet de {{entreprise}}..."),
        (10, "email", "no_reply",
         "Dernier message - bonne continuation !"),
    ]
    for day, channel, cond, tpl in defaults:
        db.add(SequenceStep(campaign_id=c.id, day_offset=day, channel=channel, condition=cond, template=tpl))
    db.commit()
    return {"id": c.id, "name": c.name, "steps": len(defaults)}


@router.post("/{campaign_id}/add-lead/{lead_id}")
def add_lead(campaign_id: int, lead_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ws_id(db, user)
    campaign = db.get(Campaign, campaign_id)
    lead = db.get(Lead, lead_id)
    if not campaign or not lead:
        raise HTTPException(404, "Campagne ou lead introuvable")
    lead.campaign_id = campaign.id
    actions = enqueue_campaign_for_lead(db, lead, campaign)
    db.commit()
    return {"lead": lead.id, "actions_queued": len(actions),
            "note": "En mode revue manuelle, la premiere action attend votre validation."}


@router.get("/actions/pending-review")
def pending_review(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws_id = _ws_id(db, user)
    rows = db.query(Action).join(Lead).filter(
        Lead.workspace_id == ws_id, Action.status == "review"
    ).all()
    return [{"id": a.id, "lead": a.lead.full_name, "channel": a.channel,
             "content": a.content, "scheduled_at": a.scheduled_at} for a in rows]


@router.post("/actions/{action_id}/approve")
def approve(action_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ws_id(db, user)
    a = db.get(Action, action_id)
    if not a:
        raise HTTPException(404, "Action introuvable")
    a.status = "pending"
    db.commit()
    return {"id": a.id, "status": a.status}


@router.get("/actions/due")
def due_actions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint consomme par l'extension Chrome : actions LinkedIn a executer."""
    ws_id = _ws_id(db, user)
    now = datetime.now(timezone.utc)
    rows = db.query(Action).join(Lead).filter(
        Lead.workspace_id == ws_id,
        Action.status == "pending",
        Action.channel.startswith("linkedin"),
        Action.scheduled_at <= now,
    ).limit(10).all()
    return [{"id": a.id, "channel": a.channel, "kind": a.kind,
             "linkedin_url": a.lead.linkedin_url, "lead_name": a.lead.full_name,
             "content": a.content} for a in rows]


@router.post("/actions/{action_id}/sent")
def mark_sent(action_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """L'extension confirme l'envoi reel sur LinkedIn."""
    _ws_id(db, user)
    a = db.get(Action, action_id)
    if not a:
        raise HTTPException(404, "Action introuvable")
    a.status = "sent"
    a.sent_at = datetime.now(timezone.utc)
    a.lead.crm_status = "contacted"
    db.commit()
    return {"id": a.id, "status": "sent"}


@router.post("/actions/{action_id}/replied")
def mark_replied(action_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Detection de reponse (via extension) : stoppe la sequence, met a jour le CRM."""
    _ws_id(db, user)
    a = db.get(Action, action_id)
    if not a:
        raise HTTPException(404, "Action introuvable")
    a.status = "replied"
    a.lead.crm_status = "replied"
    db.query(Action).filter(
        Action.lead_id == a.lead_id, Action.status == "pending"
    ).update({"status": "cancelled"})
    db.commit()
    return {"id": a.id, "status": "replied"}
