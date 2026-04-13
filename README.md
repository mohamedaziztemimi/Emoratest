# EmoraTest

AI-Powered Behavioral Intelligence for E-Commerce.

EmoraTest detects the psychological friction killing conversion, explains it in plain language grounded in behavioral science, and recommends evidence-based interventions — all in real time.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌────────────┐
│   JS SDK    │────▶│ Ingestion API│────▶│ Feature Worker   │────▶│ ML Service │
│  (< 15KB)   │     │   (FastAPI)  │     │ (8 features)     │     │ (3 models) │
└─────────────┘     └──────────────┘     └─────────────────┘     └─────┬──────┘
                                                                       │
                    ┌──────────────┐     ┌─────────────────┐           │
                    │  Dashboard   │◀────│  Dashboard API  │◀──────────┘
                    │ (React/TS)   │     │   (FastAPI)     │
                    └──────────────┘     └─────────────────┘
```

## Intelligence Layer

| Layer | Technology | Output |
|---|---|---|
| Psychology Framework | Structured JSON config | Named psychological states |
| Feature Engineering | Python, stateful session | 8-feature vector |
| ML Ensemble | XGBoost + SHAP | Intent, friction, risk score |
| Suggestion Engine | Rules-based + intervention DB | Ranked test recommendations |

## Tech Stack

| Component | Technology |
|---|---|
| Backend API | Python 3.11 / FastAPI |
| Database | Supabase (PostgreSQL) |
| ML | XGBoost / SHAP / scikit-learn |
| Frontend | React 18 / TypeScript |
| Hosting | Railway (API) / Vercel (frontend) |
| CI/CD | GitHub Actions |

## Monorepo Structure

```
├── backend/          # FastAPI backend + Alembic migrations
├── ml/               # ML training pipeline
├── frontend/         # React dashboard
└── .github/          # CI/CD workflows
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+

### Install

```bash
# All dependencies
make install

# Or individually
make install-backend
make install-ml
make install-frontend
```

### Development

```bash
make dev-backend     # Start API on :8000
make dev-frontend    # Start dashboard on :3000
```

### Lint & Test

```bash
make lint            # Ruff lint (backend + ML)
make test            # Pytest (backend + ML)
```

### Database

```bash
make migrate                          # Run migrations
make migration msg="add new table"    # Create migration
```

## Git Workflow

```
feature/CONV-XX  →  develop  →  staging  →  main
                    (CI)        (auto-deploy) (manual deploy)
```

| Branch | Purpose |
|---|---|
| `main` | Production |
| `staging` | Pre-production, auto-deploys |
| `develop` | Active development |
| `feature/*` | Individual work, PRs to develop |

## License

Proprietary — All rights reserved.
