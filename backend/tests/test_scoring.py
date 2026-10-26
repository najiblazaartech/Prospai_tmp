"""Tests du moteur de scoring explicable."""
from app.services.scoring import parse_prompt, score_lead


def test_parse_prompt_roles():
    target = parse_prompt("CEOs de scale-ups SaaS en France")
    assert "ceo" in [r.lower() for r in target["roles"]]
    assert "saas" in target["industries"]
    assert "France" in target["countries"]


def test_parse_prompt_francais():
    target = parse_prompt("directeurs commerciaux fintech")
    assert target["roles"]
    assert "fintech" in target["industries"]


def test_score_lead_parfait():
    lead = {
        "role": "CEO", "company": "SaaSFlow", "country": "France",
        "email_status": "valide",
        "enrichment": {"industry": "saas", "recent_activity": 4},
    }
    target = {"roles": ["ceo"], "industries": ["saas"], "countries": ["France"]}
    score, reasons = score_lead(lead, target)
    assert score == 100, f"score attendu 100, obtenu {score}"
    assert len(reasons) == 5  # role, secteur, activite, zone, email


def test_score_lead_faible():
    lead = {
        "role": "Developpeur", "company": "X", "country": "Allemagne",
        "email_status": "unknown", "enrichment": {},
    }
    target = {"roles": ["ceo"], "industries": ["saas"], "countries": ["France"]}
    score, reasons = score_lead(lead, target)
    assert score <= 30
    assert reasons  # toujours des raisons explicables


def test_score_plafonne_a_100():
    lead = {
        "role": "CEO", "country": "France", "email_status": "valide",
        "enrichment": {"recent_activity": 10, "industry": "saas"},
    }
    score, _ = score_lead(lead, {"roles": ["ceo"], "industries": ["saas"], "countries": ["France"]})
    assert score == 100
