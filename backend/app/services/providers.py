"""Couche providers : decouverte REELLE par defaut, replis degrades sinon.

Ordre de resolution :
1. APOLLO (si cle B2B fournie) : donnees people enrichies.
2. WEB DISCOVERY ou environnement de production : recherche web en direct.
3. En developpement/test uniquement : dataset cure ou pool de test.
"""
import json
import os
import random

from app.core.config import get_settings

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"
)

_CURATED_DATASET = "flaireprise_prospects.json"
_CURATED_KEYWORDS = [
    "flaireprise", "bodacc", "fonds de commerce", "transmission", "reprise",
    "liquidation", "redressement", "sauvegarde", "courtier", "cession",
    "expert-comptable", "expertise comptable",
]


def _load_curated(name: str) -> list:
    path = os.path.join(_DATA_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("leads", [])


def discover_leads(target: dict, limit: int = 10) -> list:
    s = get_settings()
    if s.APOLLO_API_KEY:
        return _apollo_discover(s.APOLLO_API_KEY, target, limit)

    # Production must never silently fall back to synthetic or curated data.
    # An empty prompt is not a reason to return mock records either.
    live_only = bool(s.WEB_DISCOVERY) or str(getattr(s, "ENV", "development")).lower() == "production"
    if live_only:
        if not (target.get("raw") or "").strip():
            return []
        from app.services.web_discovery import discover_web
        return discover_web(target, limit)

    return _mock_discover(target, limit)


def verify_email(email: str) -> str:
    s = get_settings()
    if s.DROPCONTACT_API_KEY:
        return _dropcontact_verify(s.DROPCONTACT_API_KEY, email)
    if email.endswith("@gmail.com") or email.endswith("@yahoo.com"):
        return "risky"
    return "valide" if email.count("@") == 1 and "." in email.split("@")[1] else "invalide"


_MOCK_POOL = [
    {"full_name": "Claire Dubois", "role": "CEO", "company": "SaaSFlow", "company_size": "45", "email": "claire@saasflow.io", "linkedin_url": "https://linkedin.com/in/claire-dubois", "enrichment": {"industry": "saas", "recent_activity": 4}},
    {"full_name": "Marc Fontaine", "role": "Head of Sales", "company": "Ledgerly", "company_size": "120", "email": "marc@ledgerly.com", "linkedin_url": "https://linkedin.com/in/marc-fontaine", "enrichment": {"industry": "fintech", "recent_activity": 3}},
    {"full_name": "Sofia Reyes", "role": "CMO", "company": "Kairos Media", "company_size": "60", "email": "sofia@gmail.com", "linkedin_url": "https://linkedin.com/in/sofia-reyes", "enrichment": {"industry": "agence", "recent_activity": 2}},
    {"full_name": "Thomas Klein", "role": "Founder", "company": "Noti", "company_size": "12", "email": "thomas@noti.app", "linkedin_url": "https://linkedin.com/in/thomas-klein", "enrichment": {"industry": "saas", "recent_activity": 1}},
    {"full_name": "Amina Cisse", "role": "VP Marketing", "company": "Doqwise", "company_size": "90", "email": "amina@doqwise.fr", "linkedin_url": "https://linkedin.com/in/amina-cisse", "enrichment": {"industry": "sante", "recent_activity": 2}},
    {"full_name": "Julien Marchand", "role": "Directeur commercial", "company": "OptiRh", "company_size": "75", "email": "julien@optirh.com", "linkedin_url": "https://linkedin.com/in/julien-marchand", "enrichment": {"industry": "saas", "recent_activity": 5}},
    {"full_name": "Laura Petit", "role": "Co-fondateur", "company": "Briz", "company_size": "20", "email": "laura@briz.io", "linkedin_url": "https://linkedin.com/in/laura-petit", "enrichment": {"industry": "e-commerce", "recent_activity": 3}},
    {"full_name": "Kevin Zhou", "role": "Directeur des ventes", "company": "Pilo", "company_size": "150", "email": "kevin@pilo.co", "linkedin_url": "https://linkedin.com/in/kevin-zhou", "enrichment": {"industry": "tech", "recent_activity": 0}},
]


def _mock_discover(target: dict, limit: int) -> list:
    prompt_text = (target.get("raw") or "").lower()
    if any(k in prompt_text for k in _CURATED_KEYWORDS):
        return _curated_discover(limit)
    leads = random.sample(_MOCK_POOL, k=min(limit, len(_MOCK_POOL)))
    out = []
    for l in leads:
        l = dict(l)
        l["country"] = (target.get("countries") or ["France"])[0]
        l["source"] = "mock"
        out.append(l)
    return out


def _curated_discover(limit: int) -> list:
    """Repli hors-ligne uniquement pour les tests / developpement."""
    out = []
    for p in _load_curated(_CURATED_DATASET)[:limit]:
        out.append({
            "full_name": p.get("decideur") or "Decideur a identifier",
            "role": p.get("segment", ""),
            "company": p.get("company", ""),
            "company_size": "",
            "email": "",
            "linkedin_url": "",
            "country": "France",
            "source": "curated-web",
            "enrichment": {
                "rank": p.get("rank"),
                "website": p.get("website", ""),
                "city": p.get("city", ""),
                "contact": p.get("contact", ""),
                "research_source": p.get("source", ""),
                "fit_detail": p.get("fit_detail", ""),
                "fit": p.get("fit", ""),
                "plan": p.get("plan", ""),
                "confidence": p.get("confidence", ""),
                "industry": p.get("segment", ""),
            },
        })
    return out


def _apollo_discover(api_key: str, target: dict, limit: int) -> list:
    import httpx
    r = httpx.post(
        "https://api.apollo.io/v1/mixed_people/search",
        json={"api_key": api_key, "page": 1, "per_page": limit,
              "person_titles": target.get("roles", []),
              "organization_locations": target.get("countries", [])},
        timeout=30,
    )
    r.raise_for_status()
    out = []
    for p in r.json().get("people", [])[:limit]:
        out.append({
            "full_name": p.get("name"),
            "role": p.get("title", ""),
            "company": p.get("organization", {}).get("name", ""),
            "company_size": str(p.get("organization", {}).get("estimated_num_employees", "")),
            "email": p.get("email", ""),
            "linkedin_url": p.get("linkedin_url", ""),
            "country": p.get("country", ""),
            "source": "apollo",
            "enrichment": {},
        })
    return out


def _dropcontact_verify(api_key: str, email: str) -> str:
    return "valide" if email else "invalide"
