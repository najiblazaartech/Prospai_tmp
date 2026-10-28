"""Decouverte web REELLE : prompt -> requetes -> moteur de recherche -> entreprises.

Aucune liste figee : a chaque recherche, le SaaS interroge le web en direct
(DuckDuckGo HTML, gratuit, sans cle), extrait les entreprises trouvees et
les deduplique par domaine. Le dataset cure n'est plus qu'un repli hors-ligne.
"""
import html as html_lib
import re
from urllib.parse import parse_qs, urlparse

import httpx

DDG_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ProspAI/1.0"

# Domaines non-entreprises a ecarter des resultats
SKIP_DOMAINS = {
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "wikipedia.org", "pagesjaunes.fr", "google.com", "bing.com",
    "duckduckgo.com", "yelp.fr", "trustpilot.com", "tripadvisor.fr",
    "societe.com", "infogreffe.fr", "bodacc.fr", "pappers.fr", "data.gouv.fr",
}

STOPWORDS = {
    "les", "des", "une", "pour", "avec", "dans", "par", "sur", "chez", "aux",
    "mon", "mes", "nos", "votre", "vos", "the", "and", "avec", "sous", "entre",
    "qui", "que", "quoi", "tout", "tous", "cette", "ce", "ceux", "en", "au",
    "et", "ou", "où", "la", "le", "du", "de", "a", "à", "d", "l",
}


def extract_keywords(prompt: str, max_keywords: int = 6) -> list:
    """Extrait les mots-cles significatifs du prompt NL."""
    words = re.findall(r"[a-zA-Zàâäéèêëîïôöùûüç\-]{3,}", prompt.lower())
    seen, out = set(), []
    for w in words:
        if w not in STOPWORDS and w not in seen:
            seen.add(w)
            out.append(w)
    return out[:max_keywords]


def build_queries(keywords: list, limit: int) -> list:
    """Genere plusieurs requetes a partir des mots-cles (diversite des sources)."""
    base = " ".join(keywords)
    suffixes = ["", "annuaire", "expert", "cabinet conseil", "avis clients"]
    queries = []
    for sfx in suffixes:
        if len(queries) * 10 >= limit + 5:
            break
        queries.append((base + " " + sfx).strip())
    return queries[:5]


def _clean_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return ""
    return host[4:] if host.startswith("www.") else host


def _base_domain(domain: str) -> str:
    parts = domain.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else domain


def _ddg_search(query: str) -> list:
    """Interroge DuckDuckGo HTML et retourne [(titre, url_reelle, snippet)]."""
    r = httpx.post(
        DDG_URL, data={"q": query},
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
        timeout=15, follow_redirects=True,
    )
    r.raise_for_status()
    page = r.text
    results = []
    links = re.findall(r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', page, re.S)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>', page, re.S)
    hrefs = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"', page)
    for (title_html, href, _snip) in zip(links, hrefs, snippets + [""] * len(links)):
        href = html_lib.unescape(href)
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        real_url = params.get("uddg", [href])[0] if params.get("uddg") else (
            "https:" + href if href.startswith("//") else href)
        title = html_lib.unescape(re.sub(r"<[^>]+>", "", title_html)).strip()
        snippet = html_lib.unescape(re.sub(r"<[^>]+>", "", _snip or "")).strip()
        results.append((title, real_url, snippet))
    return results


def discover_web(target: dict, limit: int = 10) -> list:
    """Pipeline : prompt -> requetes -> recherche live -> entreprises dedupliquees.

    Retourne [] si le reseau est indisponible (le caller bascule sur son repli).
    """
    prompt = target.get("raw") or ""
    keywords = extract_keywords(prompt)
    if not keywords:
        return []
    queries = build_queries(keywords, limit)
    seen_domains, leads = set(), []
    for q in queries:
        if len(leads) >= limit:
            break
        try:
            results = _ddg_search(q)
        except Exception:
            continue  # requete ratee -> on tente la suivante
        for title, url, snippet in results:
            domain = _clean_domain(url)
            if not domain or not title:
                continue
            if _base_domain(domain) in SKIP_DOMAINS:
                continue
            if domain in seen_domains:
                continue
            seen_domains.add(domain)
            company = (title.split(" - ")[0].split(" | ")[0].split(" — ")[0]).strip() or domain
            leads.append({
                "full_name": "Décideur à identifier",
                "role": "",
                "company": company,
                "company_size": "",
                "email": "",
                "linkedin_url": "",
                "country": "France",
                "source": "web",
                "enrichment": {
                    "website": domain,
                    "url": url,
                    "snippet": snippet[:300],
                    "search_query": q,
                    "research_source": url,
                    "industry": " ".join(keywords[:3]),
                },
            })
            if len(leads) >= limit:
                break
    return leads
