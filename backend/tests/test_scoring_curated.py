"""Test du scoring sur leads du dataset cure (fit/confiance)."""
from app.services.scoring import score_lead


def test_score_curated_lead():
    lead = {
        "company": "PIC Inter",
        "role": "Courtier fonds de commerce",
        "country": "France",
        "email": "",
        "email_status": "unknown",
        "enrichment": {"fit": "Expert", "confidence": "Élevée", "industry": "Courtier fonds de commerce"},
    }
    target = {"roles": ["founder"], "industries": [], "countries": ["France"], "raw": "transmission"}
    score, reasons = score_lead(lead, target)
    # 8 (role adjacent) + 25 (fit Expert) + 10 (confiance elevee) + 15 (zone) = 58
    assert score == 58
    assert any("Expert" in r for r in reasons)
    assert any("confiance" in r.lower() for r in reasons)


def test_score_curated_lead_pro_moyenne():
    lead = {
        "company": "Alsaeci",
        "role": "Agence fonds de commerce",
        "country": "France",
        "email": "",
        "email_status": "unknown",
        "enrichment": {"fit": "Pro", "confidence": "Moyenne"},
    }
    target = {"roles": ["founder"], "industries": [], "countries": ["France"], "raw": "transmission"}
    score, reasons = score_lead(lead, target)
    # 8 + 15 (fit Pro) + 5 (moyenne) + 15 (zone) = 43
    assert score == 43
