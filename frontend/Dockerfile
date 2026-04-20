# ────────────────────────────────────────────────────────────────
# Frontend Dockerfile - EmoraTest Next.js Application
# ────────────────────────────────────────────────────────────────

FROM node:20-alpine

WORKDIR /app

# Copy dependency files
COPY package.json package-lock.json ./

# Install dependencies (uses npm ci for reproducible builds)
# In dev mode, node_modules is preserved via anonymous volume
RUN npm ci

# Copy application code
# In dev mode, this directory is bind-mounted for hot-reload
COPY . .

EXPOSE 3000

# Development mode: hot-reload enabled via Next.js dev server
# Production mode: override CMD with ["npm", "run", "start"]
CMD ["npm", "run", "dev"]
