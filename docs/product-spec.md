---
name: "prospai-spec"
title: "ProspAI — Spécification produit"
type: "text/markdown"
---

# ProspAI — Spécification produit
*SaaS de découverte de prospects par IA + automatisation multicanale LinkedIn/email*
*Nom de code : ProspAI — positions de référence : Lessie AI (découverte IA) × Waalaxy (automatisation LinkedIn/email)*

## 1. Vision

> « Décris qui tu veux atteindre. ProspAI les trouve, les qualifie, les vérifie et lance les campagnes LinkedIn + email — de bout en bout, sans outil supplémentaire. »

**Le gap de marché** : Lessie s'arrête à l'outreach ponctuel ; Waalaxy s'arrête à l'import manuel de listes. Personne ne fait le pipeline complet *recherche IA → scoring → vérification → séquences multicanales → CRM → analytics* dans un seul produit.

## 2. Cibles (personas)

| Persona | Douleur | Valeur ProspAI |
|---|---|---|
| Founder / solo B2B | Pas de temps, pas de SDR | Pipeline de leads automatique dès le jour 1 |
| Équipe commerciale (PME/Scale-up) | Prospection manuelle, données sales | Leads enrichis, vérifiés, campagnes orchestrées |
| Agence (multi-clients) | Gérer N comptes clients | Workspaces séparés, quotas par compte, facturation agence |
| Marketer influenceur | Trouver les bons créateurs | Découverte multi-sources (TikTok, YouTube, IG, podcasts) |

## 3. Différenciation vs concurrents

| Capacité | Lessie | Waalaxy | **ProspAI** |
|---|---|---|---|
| Découverte IA multi-sources (100+ sources) | ✅ | ❌ (import manuel) | ✅ |
| Scoring / ranking des leads | ✅ | ❌ | ✅ + scoring explicable |
| Vérification email | ✅ | Via Dropcontact | ✅ natif + double provider |
| Séquences LinkedIn automatisées (invitations, relances) | ❌ | ✅ | ✅ |
| Cold email séquencé | Partiel | ✅ | ✅ |
| Workflows conditionnels multicanal | ❌ | Partiel | ✅ (si pas de réponse LinkedIn → email à J+3) |
| CRM + pipeline natif | ❌ | Synchro tierce | ✅ natif |
| Multi-comptes / agences | ❌ | Plan Team | ✅ workspaces |
| RGPD by design (consentement, logs, DPA) | Partiel | Partiel | ✅ |

**Le moat** : le scoring explicable (pourquoi ce lead est #1), les workflows multicanal conditionnels, et la boucle de feedback (les réponses aux campagnes réentraînent le scoring).

## 4. Fonctionnalités cœur (MVP → V2)

### MVP (mois 1–4)
1. **Recherche en langage naturel** — prompt → profil cible structuré (secteur, rôle, taille, zone).
2. **Découverte multi-sources** — LinkedIn (Sales Navigator), web, bases tierces (Apollo, Dropcontact), réseaux sociaux.
3. **Scoring & explication** — score 0–100 + raisons (« CEO d'une scale-up SaaS FR, actif sur LinkedIn, 3 posts sur ton sujet ce mois-ci »).
4. **Vérification email** — natif (API type Dropcontact) avec statut : valide / risky / invalide.
5. **Séquences LinkedIn** — invitations (avec message), relances, messages de suivi, quotas anti-ban (≤ 80–100/jour selon plan).
6. **Dashboard campagne** — envoyés, acceptés, réponses, taux par étape.

### V2 (mois 5–9)
7. **Cold email séquencé** — domaines de sending, warm-up, rotation de boîtes.
8. **Workflows conditionnels multicanal** — branching (réponse / pas de réponse / vu).
9. **CRM léger natif** — pipeline kanban, notes, tâches, export CSV, synchro HubSpot/Pipedrive.
10. **Boucle IA** — les outcomes réajustent le scoring ; génération de messages personnalisés par lead (hooks issus de ses posts récents).

### V3 (mois 10+)
11. Mode agence multi-workspaces, quotas et RBAC.
12. API publique + intégrations (Zapier, Make, Slack).
13. Recherche influenceurs avancée (audience estimée, engagement rate).

## 5. Conformité & sécurité (UE + international)

- **RGPD** : base légale « intérêt légitime » documenté, registre des traitements, DPA, droit à l'effacement (suppression lead + logs), données hébergées UE.
- **LinkedIn ToS** : quotas conservateurs, jitter aléatoire, simulation humaine, message d'avertissement « utiliser un compte aged », option mode « revue manuelle avant envoi » (défaut ON en EU).
- **Anti-spam email** : warm-up 2–3 semaines, DKIM/SPF/DMARC guidés, max 30–50 mails/jour/boîte au début.
- **Sécurité** : chifflement au repos, MFA, audit logs.

## 6. Pricing SaaS (indicatif)

| Plan | €/mois | Contenu |
|---|---|---|
| Starter | 49 | 1 siège, 1 compte LinkedIn, 50 crédits recherche/mois, 80 actions/j |
| Growth | 99 | 1 compte LinkedIn + 1 domaine email, 300 crédits, 200 actions/j |
| Scale | 249 | Multi-canaux, 1 000 crédits, CRM, API |
| Agency | 499 | 5 workspaces, 10 comptes, dashboard centralisé |

Le crédit recherche = 1 lead découvert + enrichi + vérifié. Pricing premium vs Waalaxy (12,50–40 €) justifié par la valeur découverte+exécution.

## 7. Risques & mitigations

| Risque | Mitigation |
|---|---|
| Ban de comptes LinkedIn clients | Quotas conservateurs, mode revue manuelle, assurance « compte aged », doc dédiée |
| Coût des APIs de données (Apollo etc.) | Mix providers, cache, crédits facturés |
| Cadre légal sur le scraping LinkedIn | Sources mixtes, data licensed providers, pas de scraping propriétaire direct |
| Dépendance à un LLM provider | Abstraction multi-provider (Mistral / OpenAI / Gemini) |