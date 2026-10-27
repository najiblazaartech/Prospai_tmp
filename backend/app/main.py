import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.routers import auth, campaigns, crm, email_accounts, search

app = FastAPI(
    title="ProspAI API",
    description="Decouverte de prospects IA + sequences multicanal LinkedIn/email",
    version="0.1.0",
)

# Configure allowed browser origins at deployment time, e.g.
# CORS_ORIGINS=https://prospai-tmp.vercel.app,http://localhost:3000
_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(search.router)
app.include_router(campaigns.router)
app.include_router(crm.router)
app.include_router(email_accounts.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "prospai-api"}
