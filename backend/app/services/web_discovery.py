"""Découverte web réelle, avec requêtes métier françaises et erreurs explicites."""
import html as html_lib
import logging
import re
from urllib.parse import parse_qs, urlparse

import httpx

logger = logging.getLogger(__name__)
DDG_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = "Mozilla/5.0 (compatible; ProspAI/1.0; +https://prospai-tmp-web.onrender.com)"

SKIP_DOMAINS = {
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "wikipedia.org", "pagesjaunes.fr", "google.com", "bing.com",
    "duckduckgo.com", "yelp.fr", "trustpilot.com", "tripadvisor.fr",
    "societe.com", "infogreffe.fr", "bodacc.fr", "pappers.fr", "data.gouv.fr",
}
STOPWORDS = {
    "les", "des", "une", "pour", "avec", "dans", "par", "sur", "chez", "aux",
    "mon", "mes", "nos", "votre", "vos", "the", "and", "sous", "entre", "qui",
    "que", "quoi", "tout", "tous", "cette", "ce", "ceux", "en", "au", "et",
    "ou", "où", "la", "le", "du", "de", "a", "à", "d", "l",
}


class WebDiscoveryError(RuntimeError):
    """Raised when the web provider cannot be queried reliably."""


def extract_keywords(prompt: str, max_keywords: int = 12) -> list:
    """Keep enough of the user's target to avoid over-narrowing French queries."""
    words = re.findall(r"[a-zA-Zàâäéèêëîïôöùûüç\-]{3,}", prompt.lower())
    seen, out = set(), []
    for word in words:
        if word not in STOPWORDS and word not in seen:
            seen.add(word)
            out.append(word)
    return out[:max_keywords]


def build_queries(keywords: list, limit: int, prompt: str = "") -> list:
    """Use both the user's wording and French business-transfer synonyms."""
    base = " ".join(keywords).strip()
    p = (prompt or "").lower()
    queries = []
    if any(term in p for term in ("transmission", "fonds de commerce", "cession", "courtiers")):
        queries.extend([
            '"cabinet transmission entreprise" France',
            '"courtier en fonds de commerce" France',
            '"cession fonds de commerce" cabinet conseil France',
            '"transmission reprise entreprise" "cabinet" France',
            'annuaire intermédiaires transmission entreprise France',
        ])
    if base:
        queries.append(base + " France")
        queries.append(base + " annuaire")
    # Preserve order and avoid repeated queries.
    unique = list(dict.fromkeys(q for q in queries if q.strip()))
    return unique[:max(3, min(8, limit))]


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
    """Fetch DuckDuckGo HTML results without relying on attribute ordering."""
    response = httpx.post(
        DDG_URL,
        data={"q": query},
        headers={"User-Agent": USER_AGENT},
        timeout=15,
        follow_redirects=True,
    )
    response.raise_for_status()
    page = response.text
    if "anomaly.js" in page.lower() or "bots use duckduckgo" in page.lower():
        raise WebDiscoveryError("DuckDuckGo a bloqué la recherche automatisée.")

    results = []
    # Attribute order varies; inspect every anchor and select result__a links.
    for match in re.finditer(r"<a\b([^>]*)>(.*?)</a>", page, re.I | re.S):
        attrs, title_html = match.group(1), match.group(2)
        if not re.search(r'class=["\'][^"\']*result__a', attrs, re.I):
            continue
        href_match = re.search(r'href=["\']([^"\']+)["\']', attrs, re.I)
        if not href_match:
            continue
        href = html_lib.unescape(href_match.group(1))
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        real_url = params.get("uddg", params.get("udd3", [href]))[0]
        if real_url.startswith("//"):
            real_url = "https:" + real_url
        title = html_lib.unescape(re.sub(r"<[^>]+>", "", title_html)).strip()
        if not title:
            continue
        results.append((title, real_url, ""))

    # Attach snippets by result order where available; missing snippets are OK.
    snippets = re.findall(
        r'class=["\'][^"\']*result__snippet[^"\']*["\'][^>]*>(.*?)</(?:a|div)>',
        page, re.I | re.S,
    )
    cleaned = [
        html_lib.unescape(re.sub(r"<[^>]+>", "", snippet)).strip()
        for snippet in snippets
    ]
    return [
        (title, url, cleaned[i] if i < len(cleaned) else snippet)
        for i, (title, url, snippet) in enumerate(results)
    ]


def discover_web(target: dict, limit: int = 10) -> list:
    """Search live web results; distinguish a genuine zero from provider failure."""
    prompt = target.get("raw") or ""
    keywords = extract_keywords(prompt)
    if not keywords:
        return []

    queries = build_queries(keywords, limit, prompt)
    seen_domains, leads = set(), []
    successful_queries = 0
    failures = []

    for query in queries:
        if len(leads) >= limit:
            break
        try:
            results = _ddg_search(query)
            successful_queries += 1
        except Exception as exc:
            failures.append(f"{query}: {type(exc).__name__}: {exc}")
            logger.warning("Web discovery query failed (%s): %s", query, exc)
            continue

        for title, url, snippet in results:
            domain = _clean_domain(url)
            if not domain or not title or _base_domain(domain) in SKIP_DOMAINS:
                continue
            if domain in seen_domains:
                continue
            seen_domains.add(domain)
            company = title.split(" - ")[0].split(" | ")[0].split(" — ")[0].strip() or domain
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
                    "search_query": query,
                    "research_source": url,
                    "industry": " ".join(keywords[:3]),
                },
            })
            if len(leads) >= limit:
                break

    if successful_queries == 0 and failures:
        # Do not mislead the UI into reporting "no matching companies" when
        # the search provider was unreachable or blocked.
        raise WebDiscoveryError("Impossible d'interroger le moteur de recherche. " + " | ".join(failures[:2]))
    logger.info("Web discovery completed: queries=%s successful=%s leads=%s", len(queries), successful_queries, len(leads))
    return leads
