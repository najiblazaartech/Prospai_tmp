from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Lead, User, Workspace, WorkspaceMember
from app.schemas import SearchRequest, LeadOut
from app.services import providers
from app.services.scoring import parse_prompt, score_lead

router = APIRouter(prefix="/search", tags=["recherche IA"])


def _get_workspace(db: Session, user: User) -> Workspace:
    m = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).first()
    if not m:
        raise HTTPException(404, "Aucun workspace")
    return db.get(Workspace, m.workspace_id)


@router.post("", response_model=list[LeadOut])
def search(body: SearchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Pipeline : prompt NL -> decouverte -> verification -> scoring explicable."""
    ws = _get_workspace(db, user)
    target = parse_prompt(body.prompt)
    candidates = providers.discover_leads(target, body.limit)

    created = []
    for c in candidates:
        email_status = providers.verify_email(c["email"]) if c.get("email") else "unknown"
        c["email_status"] = email_status
        score, reasons = score_lead(c, target)
        lead = Lead(
            workspace_id=ws.id,
            campaign_id=body.campaign_id,
            full_name=c["full_name"],
            role=c.get("role", ""),
            company=c.get("company", ""),
            company_size=c.get("company_size", ""),
            country=c.get("country", "France"),
            linkedin_url=c.get("linkedin_url", ""),
            email=c.get("email", ""),
            email_status=email_status,
            score=score,
            score_reasons=reasons,
            source=c.get("source", "mock"),
            enrichment=c.get("enrichment", {}),
        )
        db.add(lead)
        created.append(lead)
    ws.credits_remaining = max(0, ws.credits_remaining - len(created))
    db.commit()
    return sorted(created, key=lambda l: l.score, reverse=True)
