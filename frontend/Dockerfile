# ────────────────────────────────────────────────────────────────
# Frontend Dockerfile - EmoraTest Next.js Application
# ────────────────────────────────────────────────────────────────

FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Inject env at build time (CRITICAL)
ARG NEXT_PUBLIC_EMORATEST_KEY
ENV NEXT_PUBLIC_EMORATEST_KEY=$NEXT_PUBLIC_EMORATEST_KEY

# Build the application (runs ESLint too)
RUN npm run build

# ────────────────────────────────────────────────────────────────
# Production stage
# ────────────────────────────────────────────────────────────────
FROM node:20-alpine AS production

WORKDIR /app

# Copy package files and install production dependencies only
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copy built application from builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./

EXPOSE 3000

CMD ["npm", "run", "start"]
