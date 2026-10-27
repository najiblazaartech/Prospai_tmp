"""Tests d'integration de l'API (SQLite en memoire)."""
from fastapi.testclient import TestClient


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_and_me(client: TestClient):
    r = client.post("/auth/register", json={
        "email": "test@prospai.app", "password": "password123", "full_name": "Test",
    })
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token

    r = client.get("/auth/me", headers={"Authorization": "Bearer " + token})
    assert r.status_code == 200
    assert r.json()["email"] == "test@prospai.app"


def test_register_doublon(client: TestClient):
    client.post("/auth/register", json={"email": "a@b.co", "password": "password123", "full_name": ""})
    r = client.post("/auth/register", json={"email": "a@b.co", "password": "password123", "full_name": ""})
    assert r.status_code == 409


def test_login_faux(client: TestClient):
    r = client.post("/auth/login", json={"email": "x@y.co", "password": "wrongpass"})
    assert r.status_code == 401


def test_search_requires_auth(client: TestClient):
    r = client.post("/search", json={"prompt": "CEOs SaaS"})
    assert r.status_code == 401


def test_pipeline_complet(client: TestClient, monkeypatch):
    """Le pipeline CRM utilise un résultat de test contrôlé; aucune donnée fictive n'est servie en prod."""
    from app.services import providers

    monkeypatch.setattr(providers, "discover_leads", lambda target, limit: [{
        "full_name": "Prospect de test",
        "role": "CEO",
        "company": "Entreprise de test",
        "company_size": "10",
        "country": "France",
        "linkedin_url": "",
        "email": "",
        "source": "test-fixture",
        "enrichment": {"website": "https://example.test", "url": "https://example.test"},
    }][:limit])

    token = client.post("/auth/register", json={
        "email": "full@prospai.app", "password": "password123", "full_name": "Full",
    }).json()["access_token"]
    H = {"Authorization": "Bearer " + token}

    r = client.post("/search", json={"prompt": "CEOs de scale-ups SaaS en France", "limit": 5}, headers=H)
    assert r.status_code == 200
    leads = r.json()
    assert len(leads) == 1
    scores = [l["score"] for l in leads]
    assert scores == sorted(scores, reverse=True)
    assert all(l["score_reasons"] for l in leads)
    lead_id = leads[0]["id"]

    r = client.post("/campaigns", json={"name": "Campagne test", "prompt": "CEOs SaaS"}, headers=H)
    assert r.status_code == 200
    campaign_id = r.json()["id"]
    assert r.json()["steps"] == 4

    r = client.post(f"/campaigns/{campaign_id}/add-lead/{lead_id}", headers=H)
    assert r.status_code == 200
    assert r.json()["actions_queued"] == 4

    r = client.get("/campaigns/actions/pending-review", headers=H)
    assert r.status_code == 200
    review = r.json()
    assert len(review) == 1
    action_id = review[0]["id"]
    r = client.post(f"/campaigns/actions/{action_id}/approve", headers=H)
    assert r.status_code == 200
    assert r.json()["status"] == "pending"

    r = client.get("/campaigns/actions/due", headers=H)
    assert r.status_code == 200
    due = r.json()
    assert any(a["id"] == action_id for a in due)
    r = client.post(f"/campaigns/actions/{action_id}/sent", headers=H)
    assert r.status_code == 200
    r = client.post(f"/campaigns/actions/{action_id}/replied", headers=H)
    assert r.status_code == 200

    r = client.get("/crm/leads", headers=H)
    assert r.status_code == 200
    lead = [l for l in r.json() if l["id"] == lead_id][0]
    assert lead["crm_status"] == "replied"

    assert client.get("/crm/pipeline", headers=H).status_code == 200
    r = client.get("/crm/analytics", headers=H)
    assert r.status_code == 200
    assert r.json()["replies"] == 1


def test_email_account_warmup(client: TestClient):
    token = client.post("/auth/register", json={
        "email": "smtp@prospai.app", "password": "password123", "full_name": "Smtp",
    }).json()["access_token"]
    H = {"Authorization": "Bearer " + token}
    r = client.post("/email-accounts", json={
        "smtp_host": "smtp.gmail.com", "smtp_port": 587,
        "smtp_user": "test@gmail.com", "smtp_password": "apppassword", "sender_name": "Pro",
    }, headers=H)
    assert r.status_code == 200
    accounts = client.get("/email-accounts", headers=H).json()
    assert len(accounts) == 1
    assert accounts[0]["warmup_active"] is True
