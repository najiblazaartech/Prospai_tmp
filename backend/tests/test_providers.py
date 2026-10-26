"""Tests des providers mock (mode sans cle) et du dataset cure Flaireprise."""
from app.services.providers import discover_leads, verify_email


def test_discover_leads_mock():
    leads = discover_leads({"countries": ["France"]}, limit=5)
    assert 1 <= len(leads) <= 5
    for l in leads:
        assert l["full_name"]
        assert l["email"]
        assert l["source"] == "mock"


def test_verify_email_heuristique():
    assert verify_email("claire@saasflow.io") == "valide"
    assert verify_email("sofia@gmail.com") == "risky"
    assert verify_email("pasunemail") == "invalide"


def test_curated_flaireprise_dataset():
    """Un prompt ciblant l'ecosysteme transmission/FDC renvoie le dataset verifie."""
    target = {"countries": ["France"],
              "raw": "Prospects Flaireprise : courtiers fonds de commerce et cabinets de transmission en France"}
    leads = discover_leads(target, limit=10)
    assert len(leads) == 10
    for l in leads:
        assert l["source"] == "curated-web"
        assert l["company"]
        assert l["email"] == ""        # aucun email invente
        assert l["enrichment"]["website"] or l["company"]
        assert l["enrichment"]["fit"] in ("Expert", "Pro")
    assert leads[0]["company"] == "Mes Acquisitions"  # ordre de pertinence respecte


def test_curated_dataset_complet():
    """Le dataset contient les 50 prospects, servis dans l'ordre de rang."""
    leads = discover_leads({"raw": "veille BODACC liquidations et redressements"}, limit=100)
    assert len(leads) == 50
    ranks = [l["enrichment"]["rank"] for l in leads]
    assert ranks == sorted(ranks)
    assert ranks[0] == 1 and ranks[-1] == 50
    # aucun email fabrique : contact par canal public uniquement
    assert all(l["email"] == "" for l in leads)
    assert all(l["enrichment"].get("contact") for l in leads)
