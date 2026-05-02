# ────────────────────────────────────────────────────────────────
# Frontend Dockerfile - EmoraTest Next.js Application
# ────────────────────────────────────────────────────────────────

FROM node:20-alpine AS builder

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -S -u 1001 -G appuser appuser

# Copy dependency files
COPY package.json package-lock.json ./

# Install dependencies (exclude optional to avoid LGPL-licensed native binaries)
RUN npm ci --omit=optional && \
    mkdir -p .next && \
    chown -R appuser:appuser /app

# Copy application code
COPY . .

# Inject env at build time (CRITICAL)
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_EMORATEST_KEY
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_EMORATEST_KEY=$NEXT_PUBLIC_EMORATEST_KEY

# Build the application (runs ESLint too)
RUN npm run build && \
    chown -R appuser:appuser /app

# ────────────────────────────────────────────────────────────────
# Production stage
# ────────────────────────────────────────────────────────────────
FROM node:20-alpine AS production

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -S -u 1001 -G appuser appuser

# Copy package files and install production dependencies only
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --omit=optional && \
    chown -R appuser:appuser /app

# Copy built application from builder stage
COPY --from=builder --chown=appuser:appuser /app/.next ./.next
COPY --from=builder --chown=appuser:appuser /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appuser /app/public ./public
COPY --from=builder --chown=appuser:appuser /app/next.config.js ./

USER appuser

EXPOSE 3000

CMD ["npm", "run", "start"]
