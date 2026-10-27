from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import Base, engine
from app.routers import auth, campaigns, crm, email_accounts, search

settings = get_settings()

app = FastAPI(
    title="ProspAI API",
    description="Découverte de prospects IA + séquences multicanal LinkedIn/email",
    version="0.1.0",
)

allowed_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Autorise les déploiements preview/prod Vercel sans ouvrir tous les domaines.
    allow_origin_regex=r"https://[a-zA-Z0-9-]+\.vercel\.app",
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
