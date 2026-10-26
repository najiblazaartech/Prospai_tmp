from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import EmailAccount, User, WorkspaceMember
from app.services.emailer import start_warmup, send_email

router = APIRouter(prefix="/email-accounts", tags=["cold email"])


def _ws_id(db: Session, user: User) -> int:
    m = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).first()
    if not m:
        raise HTTPException(404, "Aucun workspace")
    return m.workspace_id


class EmailAccountIn(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    sender_name: str = ""


@router.get("")
def list_accounts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws_id = _ws_id(db, user)
    return [
        {"id": a.id, "smtp_host": a.smtp_host, "smtp_user": a.smtp_user,
         "daily_limit": a.daily_limit, "warmup_active": bool(a.warmup_until), "is_active": a.is_active}
        for a in db.query(EmailAccount).filter(EmailAccount.workspace_id == ws_id).all()
    ]


@router.post("")
def create_account(body: EmailAccountIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws_id = _ws_id(db, user)
    a = EmailAccount(
        workspace_id=ws_id, smtp_host=body.smtp_host, smtp_port=body.smtp_port,
        smtp_user=body.smtp_user, smtp_password=body.smtp_password, sender_name=body.sender_name,
    )
    start_warmup(a)
    db.add(a)
    db.commit()
    return {"id": a.id, "note": "Compte cree. Warm-up 14 jours demarre (5 mails/jour, puis 30). Configure SPF/DKIM/DMAP sur ton domaine."}


@router.post("/{account_id}/test")
async def test_account(account_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(EmailAccount, account_id)
    if not a:
        raise HTTPException(404, "Compte introuvable")
    ok = await send_email(a, a.smtp_user, "Test ProspAI - votre SMTP fonctionne", "Test ProspAI")
    return {"smtp_ok": ok}
