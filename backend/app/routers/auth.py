from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token, create_refresh_token, get_current_user,
    hash_password, verify_password,
)
from app.models import User, Workspace, WorkspaceMember
from app.schemas import Token, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(409, "Cet email est deja utilise")
    user = User(email=body.email, hashed_password=hash_password(body.password), full_name=body.full_name)
    db.add(user)
    db.flush()
    ws = Workspace(name="Workspace de " + (body.full_name or body.email))
    db.add(ws)
    db.flush()
    db.add(WorkspaceMember(user_id=user.id, workspace_id=ws.id, role="owner"))
    db.commit()
    return Token(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.post("/login", response_model=Token)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Email ou mot de passe incorrect")
    return Token(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "plan": user.plan}


@router.get("/workspaces")
def workspaces(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).all()
    return [{"id": m.workspace_id, "name": m.workspace.name, "role": m.role} for m in rows]
