"""Tests des providers : mode mock de developpement et decouverte live."""
from types import SimpleNamespace

from app.services import providers
from app.services.providers import discover_leads, verify_email


def test_discover_leads_mock(monkeypatch):
    monkeypatch.setattr(
        providers, "get_settings",
        lambda: SimpleNamespace(APOLLO_API_KEY="", WEB_DISCOVERY=False, ENV="development", DROPCONTACT_API_KEY=""),
    )
    leads = discover_leads({"countries": ["France"]}, limit=5)
    assert 1 <= len(leads) <= 5
    for lead in leads:
        assert lead["full_name"]
        assert lead["email"]
        assert lead["source"] == "mock"


def test_live_discovery_never_falls_back_to_mock(monkeypatch):
    """En mode live, aucun prospect fictif si la recherche web ne retourne rien."""
    monkeypatch.setattr(
        providers, "get_settings",
        lambda: SimpleNamespace(APOLLO_API_KEY="", WEB_DISCOVERY=True, ENV="development", DROPCONTACT_API_KEY=""),
    )
    monkeypatch.setattr("app.services.web_discovery.discover_web", lambda target, limit: [])
    assert discover_leads({"raw": "agences de communication B2B en France"}, limit=5) == []


def test_production_never_returns_mock_when_live_flag_is_off(monkeypatch):
    """La production reste live-only même si WEB_DISCOVERY a été oublié."""
    monkeypatch.setattr(
        providers, "get_settings",
        lambda: SimpleNamespace(APOLLO_API_KEY="", WEB_DISCOVERY=False, ENV="production", DROPCONTACT_API_KEY=""),
    )
    monkeypatch.setattr("app.services.web_discovery.discover_web", lambda target, limit: [])
    assert discover_leads({"raw": "agences de communication B2B en France"}, limit=5) == []


def test_live_discovery_without_prompt_returns_empty(monkeypatch):
    monkeypatch.setattr(
        providers, "get_settings",
        lambda: SimpleNamespace(APOLLO_API_KEY="", WEB_DISCOVERY=True, ENV="development", DROPCONTACT_API_KEY=""),
    )
    assert discover_leads({"countries": ["France"]}, limit=5) == []


def test_verify_email_heuristique(monkeypatch):
    monkeypatch.setattr(
        providers, "get_settings",
        lambda: SimpleNamespace(APOLLO_API_KEY="", WEB_DISCOVERY=False, ENV="development", DROPCONTACT_API_KEY=""),
    )
    assert verify_email("claire@saasflow.io") == "valide"
    assert verify_email("sofia@gmail.com") == "risky"
    assert verify_email("pasunemail") == "invalide"


def test_curated_flaireprise_dataset(monkeypatch):
    """Le dataset local reste uniquement accessible en mode developpement."""
    monkeypatch.setattr(
        providers, "get_settings",
        lambda: SimpleNamespace(APOLLO_API_KEY="", WEB_DISCOVERY=False, ENV="development", DROPCONTACT_API_KEY=""),
    )
    target = {"countries": ["France"],
              "raw": "Prospects Flaireprise : courtiers fonds de commerce et cabinets de transmission en France"}
    leads = discover_leads(target, limit=10)
    assert len(leads) == 10
    for lead in leads:
        assert lead["source"] == "curated-web"
        assert lead["company"]
        assert lead["email"] == ""
        assert lead["enrichment"]["website"] or lead["company"]
        assert lead["enrichment"]["fit"] in ("Expert", "Pro")
    assert leads[0]["company"] == "Mes Acquisitions"


def test_curated_dataset_complet(monkeypatch):
    """Le dataset local contient 50 entrées de test, sans email inventé."""
    monkeypatch.setattr(
        providers, "get_settings",
        lambda: SimpleNamespace(APOLLO_API_KEY="", WEB_DISCOVERY=False, ENV="development", DROPCONTACT_API_KEY=""),
    )
    leads = discover_leads({"raw": "veille BODACC liquidations et redressements"}, limit=100)
    assert len(leads) == 50
    ranks = [lead["enrichment"]["rank"] for lead in leads]
    assert ranks == sorted(ranks)
    assert ranks[0] == 1 and ranks[-1] == 50
    assert all(lead["email"] == "" for lead in leads)
    assert all(lead["enrichment"].get("research_source") for lead in leads)
