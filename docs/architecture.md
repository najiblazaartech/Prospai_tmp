---
name: "prospai-architecture"
title: "ProspAI — Architecture technique & roadmap"
type: "text/markdown"
---

# ProspAI — Architecture technique & roadmap

## 1. Vue d'ensemble

Approche **mixte** : on construit le cœur (agents IA, moteur de séquences, scoring) et on connecte les providers existants pour les données (Apollo, Dropcontact) et le sending.

```mermaid
flowchart TD
  subgraph Front
    Web["Web app (Next.js)"]
    Ext["Extension Chrome"]
  end
  subgraph Core["Cœur propriétaire"]
    API["API Gateway (FastAPI)"]
    Orch["Orchestrateur multi-agents"]
    Score["Moteur de scoring"]
    Seq["Moteur de séquences"]
    CRM["CRM & pipeline"]
  end
  subgraph Workers["Workers async"]
    Disc["Agents de découverte"]
    Enr["Agents d'enrichissement"]
    Ver["Vérification email"]
    Send["Workers d'envoi (jitter)"]
  end
  subgraph Externe["Providers (build vs buy)"]
    Li["Extension → actions LinkedIn"]
    AP["Apollo / providers B2B"]
    DC["Dropcontact (emails RGPD)"]
    LLM["LLM (Mistral / multi-provider)"]
    Mail["Infra email (Postfix/SMTP warm-up)"]
  end
  Web --> API
  Ext -->|actions humain-like| Li
  API --> Orch
  Orch --> Disc
  Orch --> Enr
  Orch --> Ver
  Disc --> AP
  Ver --> DC
  Enr --> LLM
  Score --> CRM
  Orch --> Score
  CRM --> Seq
  Seq --> Send
  Send --> Li
  Send --> Mail
```

## 2. Stack recommandée

| Couche | Choix | Pourquoi |
|---|---|---|
| Front | Next.js + Tailwind + shadcn | Rapide, moderne, SEO landing |
| Extension Chrome | React + Manifest V3 | Actions LinkedIn côté client (comme Waalaxy) |
| API | Python FastAPI | Écosystème IA, async natif |
| Orchestrateur | Temporal (ou Celery) | Séquences fiables, retries, timers J+1/J+3 |
| Agents IA | Mistral API (abstraction multi-provider) | Coût/vitesse, flexibilité |
| DB | PostgreSQL + pgvector | CRM + recherche sémantique de leads |
| Cache/queues | Redis | Jobs, rate-limiting, jitter |
| Infra | Fly.io ou AWS eu-west-3 (UE) | RGPD : hébergement UE par défaut |
| Observabilité | Grafana + Sentry | Monitoring quotas/bans |

## 3. Pipeline de découverte (rôle des agents)

```mermaid
sequenceDiagram
  participant U as Utilisateur
  participant O as Orchestrateur
  participant D as Agent Scout
  participant E as Agent Enrichisseur
  participant V as Agent Vérificateur
  participant S as Scoring
  participant X as Moteur de séquences
  U->>O: Prompt NL ("CEOs SaaS série A en France")
  O->>D: Profil cible structuré
  D->>D: Recherche 100+ sources (LinkedIn, web, bases)
  D->>E: Candidats bruts
  E->>E: Enrichissement (rôle, société, posts récents)
  E->>V: Profil complet
  V->>V: Email vérifié (valide / risky / invalide)
  V->>S: Lead + données
  S-->>U: Shortlist scorée + raisons
  U->>X: Ajouter à la séquence (revue manuelle en EU)
```

## 4. Moteur de séquences multicanal

```mermaid
stateDiagram-v2
  [*] --> EnAttente
  EnAttente --> InvitationJ0 : Jour 0
  InvitationJ0 --> RelanceJ3 : Pas de réponse (J+3)
  RelanceJ3 --> MessageJ7 : Accepté
  RelanceJ3 --> EmailJ5 : Pas accepté (J+5)
  MessageJ7 --> EmailJ10 : Pas de réponse
  EmailJ10 --> [*] : Réponse → CRM
  MessageJ7 --> [*] : Réponse → CRM
```

- Chaque action passe par la **file avec jitter** (fenêtres horaires, délais aléatoires 30–90 s, quotas quotidiens).
- En mode EU, défaut : **revue manuelle** avant la première vague d'envois.

## 5. Modèle de données (extrait)

```mermaid
erDiagram
  WORKSPACE ||--o{ CAMPAIGN : has
  CAMPAIGN ||--o{ SEQUENCE : contains
  SEQUENCE ||--o{ STEP : has
  CAMPAIGN ||--o{ LEAD : targets
  LEAD ||--o{ ACTION : receives
  LEAD }o--|| PERSON : "refers to"
  PERSON ||--o{ ENRICHMENT : has
  ACTION }o--|| STEP : executes
  LEAD ||--o{ REPLY : receives
  REPLY ||--o| FEEDBACK : generates
  FEEDBACK ||--o| SCORE_MODEL : retrains
  LEAD {
    uuid id
    uuid person_id
    uuid campaign_id
    int score
    text score_reasons
    text email_status
  }
```

## 6. Roadmap (6 mois)

```mermaid
gantt
  title Roadmap ProspAI — 6 mois
  dateFormat YYYY-MM-DD
  section Fondations
  Design system + API squelette :f1, 2026-11-02, 3w
  Auth, workspaces, billing (Stripe) :f2, after f1, 2w
  section MVP découverte
  Agent scout (Apollo + web) :m1, after f2, 3w
  Scoring + enrichissement + emails (Dropcontact) :m2, after m1, 3w
  section MVP exécution
  Extension Chrome (invitations + messages) :e1, after m2, 4w
  Moteur de séquences (Temporal) :e2, after e1, 3w
  section Beta
  Beta privée 20 utilisateurs :b1, after e2, 4w
  Boucle de feedback scoring :b2, after b1, 3w
  section Lancement
  Cold email séquencé + warm-up :l1, after b2, 4w
  Lancement public :milestone, after l1, 0d
```

## 7. Make ou buy — arbitrages clés

| Brique | Décision | Raison |
|---|---|---|
| Données B2B | **Buy** (Apollo + 1 backup) | Coût scraping légal >> API |
| Emails vérifiés | **Buy** (Dropcontact, EU) | RGPD + qualité |
| Scoring + agents | **Build** | Le moat produit |
| Moteur de séquences | **Build** sur Temporal | Cœur différenciant |
| Actions LinkedIn | **Build** extension (pas d'API officielle) | Seule voie viable, comme Waalaxy |
| LLM | **Buy** avec abstraction | Multi-provider, contrôle des coûts |