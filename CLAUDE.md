# EmoraTest — Global Rules

## What is this project
EmoraTest is an Emotion ML + A/B Testing SaaS platform.
Tagline: "Unlock Emotions, Win Tests"
Brand colors: #007BFF (blue) + #7C3AED (purple)
DO NOT call it Conversiono anywhere — that is the old name.

## Stack
- Frontend: Next.js 14, TypeScript, Tailwind CSS, port 3000
- Backend: FastAPI (Python 3.11), PostgreSQL, Redis, port 8000
- ML: scikit-learn / XGBoost emotion classifier
- Infra: Docker Compose (all 4 services)

## Running locally
docker-compose up
Frontend: http://localhost:3000
Backend: http://localhost:8000
API docs: http://localhost:8000/docs

## Project structure
frontend/src/app/(landing)/     → public landing page
frontend/src/app/(auth)/        → login, signup pages
frontend/src/app/dashboard/     → authenticated product
frontend/src/components/        → shared components
backend/app/api/                → FastAPI routes
backend/app/models/             → SQLAlchemy models
backend/app/services/           → business logic
backend/app/api/webhook.py      → integrations
ml/src/emotion_classifier.py    → 8-emotion ML model
ml/src/feature_extractor.py     → behavioral features

## Auth
- JWT tokens stored in httpOnly cookies
- Protected routes: /dashboard/* requires valid JWT
- Public routes: / /login /signup /pricing /docs /blog
- Middleware at frontend/src/middleware.ts handles redirect

## Environment variables
Frontend needs: NEXT_PUBLIC_API_URL=http://localhost:8000
Backend needs: DATABASE_URL, REDIS_URL, SECRET_KEY
Never hardcode secrets — always use .env files

## Naming conventions
- React components: PascalCase
- API routes: snake_case
- DB columns: snake_case
- CSS classes: kebab-case
- TypeScript interfaces: PascalCase with I prefix optional

## Git rules
- Never commit .env files
- Never commit node_modules
- Branch naming: feature/xxx, fix/xxx, chore/xxx