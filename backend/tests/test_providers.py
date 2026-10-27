"""Provider tests: user-facing searches must not invent prospect records."""
from app.services.providers import discover_leads, verify_email

def test_discovery_disabled_returns_no_synthetic_leads(monkeypatch):
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "WEB_DISCOVERY", False)
    monkeypatch.setattr(settings, "APOLLO_API_KEY", "")
    assert discover_leads({"countries": ["France"], "raw": "CEO SaaS France"}, limit=5) == []

def test_verify_email_heuristique():
    assert verify_email("claire@saasflow.io") == "valide"
    assert verify_email("sofia@gmail.com") == "risky"
    assert verify_email("pasunemail") == "invalide"

def test_live_discovery_returns_provider_results(monkeypatch):
    from app.core.config import get_settings
    from app.services import web_discovery
    settings = get_settings()
    monkeypatch.setattr(settings, "WEB_DISCOVERY", True)
    monkeypatch.setattr(settings, "APOLLO_API_KEY", "")
    sample = [{"full_name": "Décideur à identifier", "company": "Entreprise trouvée sur le web", "source": "web", "enrichment": {"website": "example.org"}}]
    monkeypatch.setattr(web_discovery, "discover_web", lambda target, limit: sample)
    assert discover_leads({"raw": "entreprises France"}, limit=1) == sample
