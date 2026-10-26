"""Moteur de scoring explicable : signaux -> score 0-100 + raisons."""
import re

WEIGHTS = {
    "role_match": 30,
    "company_fit": 20,
    "activity": 20,
    "geography": 15,
    "email_quality": 15,
    "curated_fit": 25,
    "curated_confidence": 10,
}


def score_lead(lead: dict, target: dict) -> tuple:
    """Retourne (score, raisons). target = profil cible issu du prompt NL."""
    score, reasons = 0, []

    if target.get("roles") and any(r.lower() in (lead.get("role") or "").lower() for r in target["roles"]):
        score += WEIGHTS["role_match"]
        reasons.append("Role recherche (" + lead.get("role", "") + ")")
    else:
        score += 8
        reasons.append("Role adjacent")

    enr = lead.get("enrichment") or {}

    if target.get("industries") and any(
        i.lower() in (lead.get("industry") or enr.get("industry") or "").lower()
        for i in target["industries"]
    ):
        score += WEIGHTS["company_fit"]
        reasons.append("Secteur cible (" + lead.get("company", "") + ")")

    # Fit produit et confiance issus d'une recherche web verifiee (dataset cure)
    fit = (enr.get("fit") or "").lower()
    if fit == "expert":
        score += WEIGHTS["curated_fit"]
        reasons.append("Fit produit Expert (recherche web verifiee)")
    elif fit == "pro":
        score += int(WEIGHTS["curated_fit"] * 0.6)
        reasons.append("Fit produit Pro (recherche web verifiee)")

    conf = (enr.get("confidence") or "").lower().replace("é", "e")
    if conf == "elevee":
        score += WEIGHTS["curated_confidence"]
        reasons.append("Donnees verifiees (confiance elevee)")
    elif conf == "moyenne":
        score += 5
        reasons.append("Confiance moyenne")

    activity = enr.get("recent_activity", 0)
    if activity >= 3:
        score += WEIGHTS["activity"]
        reasons.append("Tres actif (" + str(activity) + " posts/signaux ce mois-ci)")
    elif activity >= 1:
        score += 10
        reasons.append("Activite moderee detectee")

    if target.get("countries") and lead.get("country") in target["countries"]:
        score += WEIGHTS["geography"]
        reasons.append("Zone cible (" + lead.get("country", "") + ")")

    if lead.get("email_status") == "valide":
        score += WEIGHTS["email_quality"]
        reasons.append("Email verifie valide")
    elif lead.get("email_status") == "risky":
        score += 6
        reasons.append("Email risque")

    return min(score, 100), reasons


# --- Parsing NL simple (remplace par LLM si MISTRAL_API_KEY fourni) ---
ROLE_KEYWORDS = {
    "ceo": ["ceo", "fondateur", "founder", "president"],
    "head of sales": ["head of sales", "directeur commercial", "directeur des ventes"],
    "cmo": ["cmo", "directeur marketing"],
    "founder": ["founder", "fondateur", "co-fondateur"],
    "sales": ["sales", "commercial", "sdr", "business development"],
    "marketing": ["marketing", "growth"],
}


def parse_prompt(prompt: str) -> dict:
    """Transforme un prompt NL en profil cible structure (fallback sans LLM)."""
    p = prompt.lower()
    roles = [role for role, kws in ROLE_KEYWORDS.items() if any(k in p for k in kws)]
    industries = []
    for ind in ["saas", "fintech", "sante", "health", "e-commerce", "agence", "tech"]:
        if ind in p:
            industries.append(ind)
    countries = []
    for c in ["france", "belgique", "suisse", "europe"]:
        if c in p:
            countries.append(c.capitalize())
    size_match = re.search(r"(\d+)\s*(?:a|-|a)\s*(\d+)", p)
    return {
        "roles": roles or ["founder", "ceo"],
        "industries": industries,
        "countries": countries or ["France"],
        "size_range": [int(size_match.group(1)), int(size_match.group(2))] if size_match else None,
        "raw": prompt,
    }
