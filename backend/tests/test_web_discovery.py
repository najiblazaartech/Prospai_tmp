"""Tests du moteur de decouverte web (HTML factice, aucun reseau requis)."""
from types import SimpleNamespace

from app.services import web_discovery


FAKE_HTML = """
<a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?udd3=https%3A%2F%2Fwww.mesacquisitions.com%2Fannonces&amp;rut=abc123">Mes Acquisitions - Annonces de reprise</a>
<a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?udd3=https%3A%2F%2Fwww.linkedin.com%2Fcompany%2Fpic-inter">PIC Inter - LinkedIn</a>
<a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?udd3=https%3A%2F%2Fwww.groupe-ftc.com%2F&amp;rut=def">Groupe FTC | Fonds de commerce CHR</a>
<a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?udd3=https%3A%2F%2Fwww.mesacquisitions.com%2F&amp;rut=xyz">Mes Acquisitions (doublon domaine)</a>
"""


def test_extract_keywords():
    kws = web_discovery.extract_keywords("Prospects Flaireprise : courtiers fonds de commerce en France")
    assert "courtiers" in kws
    assert "les" not in kws and "pour" not in kws


def test_build_queries():
    qs = web_discovery.build_queries(["courtiers", "fonds", "commerce"], limit=10)
    assert qs and all(isinstance(q, str) for q in qs)


def test_discover_web_parse_et_dedup(monkeypatch):
    """Parse les resultats DDG, ecarte LinkedIn et deduplique par domaine."""
    def fake_post(url, data=None, headers=None, timeout=None, follow_redirects=None):
        return SimpleNamespace(text=FAKE_HTML, raise_for_status=lambda: None)
    monkeypatch.setattr(web_discovery.httpx, "post", fake_post)

    leads = web_discovery.discover_web(
        {"raw": "courtiers fonds de commerce france"}, limit=10)
    domains = [l["enrichment"]["website"] for l in leads]
    assert "mesacquisitions.com" in domains
    assert "groupe-ftc.com" in domains
    assert "linkedin.com" not in domains           # plateformes ecartees
    assert len(domains) == len(set(domains))       # dedup par domaine
    for l in leads:
        assert l["source"] == "web"
        assert l["company"]
        assert l["email"] == ""                    # aucun email invente
        assert l["enrichment"]["url"].startswith("https://")


def test_discover_web_reseau_indisponible(monkeypatch):
    """Si le reseau echoue, retourne [] (le caller bascule sur son repli)."""
    def fake_post(*a, **k):
        raise ConnectionError("no network")
    monkeypatch.setattr(web_discovery.httpx, "post", fake_post)
    leads = web_discovery.discover_web({"raw": "courtiers fonds de commerce"}, limit=10)
    assert leads == []


def test_discover_leads_chaine_de_resolution(monkeypatch):
    """WEB_DISCOVERY on -> web live ; sans reseau -> aucun faux resultat."""
    from app.services import providers

    def fake_post(url, data=None, headers=None, timeout=None, follow_redirects=None):
        return SimpleNamespace(text=FAKE_HTML, raise_for_status=lambda: None)

    fake_settings = SimpleNamespace(APOLLO_API_KEY="", WEB_DISCOVERY=True)
    monkeypatch.setattr(providers, "get_settings", lambda: fake_settings)
    monkeypatch.setattr(web_discovery.httpx, "post", fake_post)
    target = {"countries": ["France"], "raw": "courtiers fonds de commerce transmission",
              "roles": ["founder"], "industries": []}
    leads = providers.discover_leads(target, limit=10)
    assert leads and all(l["source"] == "web" for l in leads)

    # Sans reseau : aucune substitution par des donnees hors ligne.
    def no_network(*a, **k):
        raise ConnectionError("no network")
    monkeypatch.setattr(web_discovery.httpx, "post", no_network)
    leads = providers.discover_leads(target, limit=10)
    assert leads == []
