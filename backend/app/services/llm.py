"""Couche LLM : Mistral (tier gratuit sur La Plateforme) avec fallback sans cle.

Cle gratuite : https://console.mistral.ai/ (tier free avec limites de debit).
Si MISTRAL_API_KEY est vide, on retombe sur le parsing heuristique + modeles simples.
"""
import httpx

from app.core.config import get_settings

SYSTEM_PROMPT = (
    "Tu es un assistant de prospection B2B. Tu ecris des messages courts, "
    "personnalises et naturels en francais, sans jargon commercial agressif."
)


async def llm_complete(prompt: str, system: str = SYSTEM_PROMPT, max_tokens: int = 300) -> str:
    """Appelle Mistral. Retourne None si pas de cle (le caller gere le fallback)."""
    s = get_settings()
    if not s.MISTRAL_API_KEY:
        return None
    try:
        r = await _chat(s.MISTRAL_API_KEY, system, prompt, max_tokens)
        return r
    except Exception:
        return None


async def _chat(api_key: str, system: str, prompt: str, max_tokens: int) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": "Bearer " + api_key},
            json={
                "model": "mistral-small-latest",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.6,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def parse_prompt_llm(prompt: str) -> dict:
    """Parsing NL du profil cible via LLM, avec fallback heuristique."""
    from app.services.scoring import parse_prompt
    schema = (
        "Extrais le profil cible en JSON strict : "
        '{"roles": [...], "industries": [...], "countries": [...]}. '
        "Prompt : " + prompt
    )
    import json as _json
    out = await llm_complete(schema, system="Tu renvoies uniquement du JSON valide, sans texte autour.")
    if out:
        try:
            start, end = out.find("{"), out.rfind("}")
            data = _json.loads(out[start:end + 1])
            data.setdefault("raw", prompt)
            return data
        except Exception:
            pass
    return parse_prompt(prompt)


async def generate_message(lead: dict, template_hint: str) -> str:
    """Message personnalise via LLM, fallback sur le rendu de template."""
    prompt = (
        "Ecris un message LinkedIn/email court (max 60 mots) pour prospecter :\n"
        "- Nom : {nom}\n- Role : {role}\n- Entreprise : {entreprise}\n"
        "- Signaux : {signaux}\n- Intention : {hint}\n"
        "Ton naturel, une seule question a la fin, pas de pitch produit."
    ).format(
        nom=lead.get("full_name", ""), role=lead.get("role", ""),
        entreprise=lead.get("company", ""),
        signaux=str((lead.get("enrichment") or {}).get("industry", "")),
        hint=template_hint[:200],
    )
    out = await llm_complete(prompt, max_tokens=200)
    return out or template_hint
