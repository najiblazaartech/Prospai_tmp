# ProspAI

**SaaS de decouverte de prospects par IA + automatisation multicanale (LinkedIn + email).**
Decris ta cible en langage naturel -> ProspAI la trouve, la score, la verifie et lance les campagnes.

> Vision : Lessie (decouverte IA) x Waalaxy (sequences LinkedIn/email) dans un seul produit.

## Demarrage rapide (100% gratuit, sans aucune cle payante)

```bash
cp .env.example .env
docker compose up --build
# Frontend : http://localhost:3000
# API      : http://localhost:8000/docs
```

Compte demo cree automatiquement : **demo@prospai.app / prospai123**

Sans aucune cle API, tout fonctionne en mode demo :
- Recherche IA avec parsing heuristique du prompt et pool de leads fictifs
- Scoring explicable, verification email heuristique
- Sequences multicanal simulees (mode mock), CRM, analytics

## Cles gratuites optionnelles

| Fonction | Cle gratuite | Ou la prendre |
|---|---|---|
| LLM (parsing du prompt + messages personnalises) | **Mistral La Plateforme, tier gratuit** | https://console.mistral.ai/ |
| LLM alternatif gratuit | Gemini / Groq tiers gratuits | https://aistudio.google.com / https://console.groq.com |
| Cold email reel | **Gmail app-password** ou Brevo (300/jour gratuits) | Google compte -> Securite -> MDP d'application |
| Donnees B2B reelles (Apollo) | payant (optionnel) | https://www.apollo.io/ |
| Emails verifies (Dropcontact, RGPD) | payant (optionnel) | https://dropcontact.io/ |

Mettez `MISTRAL_API_KEY` dans `.env` pour activer le parsing LLM du prompt et la
generation de messages personnalises (fallback automatique si quota depasse).

## Extension Chrome (actions LinkedIn reelles)

1. Chrome -> `chrome://extensions` -> Mode developpeur -> "Charger l'extension non empactee" -> dossier `extension/`
2. Connectez-vous avec votre compte ProspAI dans le popup de l'extension
3. L'extension recupere les actions dues toutes les 10 min (`/campaigns/actions/due`),
   ouvre chaque profil et execute l'invitation/le message (frappe humain-like, jitter 15-60 s)
4. Les envois sont confirmes a l'API (`/sent`) ; une reponse detectee stoppe la sequence (`/replied`)

**Securite LinkedIn** : utilisez un compte aged, ne depassez pas 80 actions/jour
(quota par defaut), laissez le jitter actif. Le mode revue manuelle (RGPD) vous fait
valider chaque premiere action avant tout envoi.

## Cold email reel

Ajoutez un compte SMTP (Gmail app-password ou Brevo gratuit) depuis
`POST /email-accounts` ou l'API Swagger. Le warm-up de 14 jours demarre
automatiquement (5 mails/jour puis 30) avec delis aleatoires anti-spam.
Configurez SPF/DKIM/DMARC sur votre domaine d'envoi.

## Architecture

```
prospai/
├── backend/        # API FastAPI : auth JWT, recherche IA, scoring, sequences, SMTP, LLM
├── frontend/       # App Next.js : dashboard recherche IA / campagnes / validation / CRM
├── extension/      # Extension Chrome : automatisation DOM LinkedIn
├── docs/           # Spec produit & architecture
└── .github/        # CI (lint backend + build frontend)
```

## Modules cles

- Recherche IA : prompt NL -> profil cible -> leads scores avec explications
- Scoring explicable : score 0-100 + raisons (role, secteur, activite, zone, email)
- Sequences multicanal conditionnelles : J0 invitation, J+3 relance, J+5 email, J+10 breakup
- Worker : envoi SMTP reel + simulation LinkedIn (ou extension si connectee)
- CRM kanban + analytics + mode revue manuelle RGPD par defaut

## Conformite

RGPD : revue manuelle par defaut, interet legitime documente, suppresion lead possible.
LinkedIn : quotas conservateurs, jitter humain, recommandation de compte aged.
