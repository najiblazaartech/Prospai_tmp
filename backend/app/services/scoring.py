"""Moteur de scoring explicable : signaux -> score 0-100 + raisons."""
import re
import unicodedata

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


ROLE_KEYWORDS = {
    "ceo": ["ceo", "fondateur", "founder", "president", "président", "chief executive"],
    "head of sales": ["head of sales", "directeur commercial", "directeur des ventes", "sales director"],
    "cmo": ["cmo", "directeur marketing", "chief marketing"],
    "founder": ["founder", "fondateur", "co-fondateur", "cofounder"],
    "sales": ["sales", "commercial", "sdr", "business development"],
    "marketing": ["marketing", "growth"],
}

# Alias français et anglais normalisés vers des libellés stables.
COUNTRY_ALIASES = {
    "France": ["france", "french"],
    "Belgium": ["belgique", "belgium", "belgian"],
    "Switzerland": ["suisse", "switzerland", "swiss"],
    "United Kingdom": ["royaume-uni", "royaume uni", "uk", "united kingdom", "britain", "british", "angleterre", "england"],
    "United States": ["états-unis", "etats-unis", "united states", "usa", "u.s.a.", "us market", "america", "american"],
    "Canada": ["canada", "canadian"],
    "Germany": ["allemagne", "germany", "german"],
    "Spain": ["espagne", "spain", "spanish"],
    "Italy": ["italie", "italy", "italian"],
    "Netherlands": ["pays-bas", "pays bas", "netherlands", "dutch", "holland"],
    "Portugal": ["portugal", "portuguese"],
    "Morocco": ["maroc", "morocco", "moroccan"],
    "Ireland": ["irlande", "ireland", "irish"],
    "Luxembourg": ["luxembourg"],
    "United Arab Emirates": ["émirats arabes unis", "emirats arabes unis", "uae", "united arab emirates", "dubai", "dubaï"],
    "Australia": ["australie", "australia", "australian"],
    "India": ["inde", "india", "indian"],
    "Brazil": ["brésil", "bresil", "brazil", "brazilian"],
    "Mexico": ["mexique", "mexico", "mexican"],
    "Singapore": ["singapour", "singapore"],
    "Japan": ["japon", "japan", "japanese"],
    "China": ["chine", "china", "chinese"],
    "Sweden": ["suède", "suede", "sweden", "swedish"],
    "Norway": ["norvège", "norvege", "norway", "norwegian"],
    "Denmark": ["danemark", "denmark", "danish"],
    "Poland": ["pologne", "poland", "polish"],
    "Austria": ["autriche", "austria", "austrian"],
    "Turkey": ["turquie", "turkey", "turkish"],
    "South Africa": ["afrique du sud", "south africa"],
    "Global": ["international", "internationally", "worldwide", "global", "tous les pays", "all countries"],
    "Europe": ["europe", "européen", "european"],
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def parse_prompt(prompt: str) -> dict:
    """Transforme un prompt NL en profil cible, sans imposer la France par défaut."""
    p = prompt.lower()
    normalized = _normalize(p)
    roles = [role for role, kws in ROLE_KEYWORDS.items() if any(k in p for k in kws)]
    industries = []
    for ind in ["saas", "fintech", "sante", "santé", "health", "e-commerce", "agence", "tech"]:
        if ind in p:
            industries.append(ind)

    countries = []
    normalized_padded = " " + normalized.replace("-", " ") + " "
    for country, aliases in COUNTRY_ALIASES.items():
        for alias in aliases:
            alias_norm = _normalize(alias).replace("-", " ")
            # Boundaries prevent e.g. "us" matching inside unrelated words.
            if re.search(r"(?<![a-z])" + re.escape(alias_norm) + r"(?![a-z])", normalized_padded):
                countries.append(country)
                break
    countries = list(dict.fromkeys(countries))

    size_match = re.search(r"(\d+)\s*(?:a|-|à)\s*(\d+)", p)
    return {
        "roles": roles or ["founder", "ceo"],
        "industries": list(dict.fromkeys(industries)),
        "countries": countries,
        "size_range": [int(size_match.group(1)), int(size_match.group(2))] if size_match else None,
        "raw": prompt,
    }
