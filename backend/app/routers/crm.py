from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Action, Lead, User, WorkspaceMember

router = APIRouter(prefix="/crm", tags=["CRM"])


def _ws_id(db: Session, user: User) -> int:
    m = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).first()
    return m.workspace_id


@router.get("/leads")
def leads(status: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws_id = _ws_id(db, user)
    q = db.query(Lead).filter(Lead.workspace_id == ws_id)
    if status:
        q = q.filter(Lead.crm_status == status)
    return [{
        "id": l.id, "name": l.full_name, "role": l.role, "company": l.company,
        "score": l.score, "reasons": l.score_reasons, "email": l.email,
        "email_status": l.email_status, "crm_status": l.crm_status,
        "campaign_id": l.campaign_id, "linkedin_url": l.linkedin_url,
    } for l in q.order_by(Lead.score.desc()).all()]


@router.patch("/leads/{lead_id}/status")
def set_status(lead_id: int, status: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        return {"error": "not found"}
    lead.crm_status = status
    db.commit()
    return {"id": lead.id, "crm_status": lead.crm_status}


@router.get("/pipeline")
def pipeline(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws_id = _ws_id(db, user)
    statuses = ["new", "contacted", "replied", "meeting", "won", "lost"]
    return [{"status": s,
             "count": db.query(Lead).filter(Lead.workspace_id == ws_id, Lead.crm_status == s).count()}
            for s in statuses]


@router.get("/analytics")
def analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws_id = _ws_id(db, user)
    total = db.query(Lead).filter(Lead.workspace_id == ws_id).count()
    replied = db.query(Lead).filter(Lead.workspace_id == ws_id, Lead.crm_status == "replied").count()
    sent_actions = db.query(Action).join(Lead).filter(
        Lead.workspace_id == ws_id, Action.sent_at.isnot(None)).count()
    return {
        "total_leads": total, "actions_sent": sent_actions, "replies": replied,
        "reply_rate": round(replied / total * 100, 1) if total else 0,
    }
