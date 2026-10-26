"""Seed : compte de demo pret a l'emploi."""
import os

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Campaign, SequenceStep, User, Workspace, WorkspaceMember

DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@prospai.app")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "prospai123")

_STEPS = [(0, "linkedin_invitation", "always"), (3, "linkedin_message", "no_reply"),
          (5, "email", "not_accepted"), (10, "email", "no_reply")]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(User).filter(User.email == DEMO_EMAIL).first():
        db.close()
        return
    user = User(email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD),
                full_name="Demo", plan="growth")
    ws = Workspace(name="Workspace Demo")
    db.add(user); db.flush()
    db.add(ws); db.flush()
    db.add(WorkspaceMember(user_id=user.id, workspace_id=ws.id, role="owner"))

    for name, prompt in [
        ("CEOs SaaS FR - Vague 1", "CEOs de scale-ups SaaS en France"),
        ("Flaireprise - Radar BODACC", "Prospects Flaireprise : courtiers fonds de commerce, "
         "cabinets de transmission PME et experts-comptables en France"),
    ]:
        c = Campaign(workspace_id=ws.id, name=name, prompt=prompt)
        db.add(c); db.flush()
        for day, ch, cond in _STEPS:
            db.add(SequenceStep(campaign_id=c.id, day_offset=day, channel=ch, condition=cond))
    db.commit()
    db.close()
    print("Seed OK - demo:", DEMO_EMAIL, "/", DEMO_PASSWORD)


if __name__ == "__main__":
    seed()
