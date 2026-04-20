# Hot-Reload Development Setup

This project now supports instant hot-reload for local development. Any code changes you make are immediately reflected in the running containers.

## How It Works

**Development Mode** (`docker compose up`):
- Automatically merges `docker-compose.yml` + `docker-compose.override.yml`
- Your local source code is bind-mounted into containers
- Dependencies (`node_modules`, `site-packages`) are preserved in anonymous volumes
- Changes trigger automatic restart/refresh

**Production Mode** (`docker compose -f docker-compose.yml up`):
- Uses only `docker-compose.yml` (ignores override file)
- Code is baked into the image (no bind mounts)
- No hot-reload overhead

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `docker-compose.override.yml` | Dev-only config with bind mounts and dependency volumes |
| `frontend/.dockerignore` | Excludes unnecessary files from frontend builds |
| `backend/.dockerignore` | Excludes unnecessary files from backend builds |
| `ml/.dockerignore` | Excludes unnecessary files from ML builds |

### Modified Files

| File | Changes |
|------|---------|
| `docker-compose.yml` | Removed inline volumes, added documentation |
| `frontend/Dockerfile` | Added comments explaining dev vs production CMD |
| `backend/Dockerfile` | Added comments, installed gcc for compiled dependencies |

## Quick Start

1. **Start containers with hot-reload:**
   ```bash
   docker compose up --build
   ```

2. **Edit any source file locally** - the change is instantly picked up:
   - Frontend: Edit `frontend/src/...` → browser auto-refreshes
   - Backend: Edit `backend/app/...` → server auto-restarts

3. **View logs in real-time:**
   ```bash
   docker compose logs -f backend frontend
   ```

## Volume Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Host Machine                         │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ frontend/src/   │  │ backend/app/    │                   │
│  │   (your edits)  │  │   (your edits)  │                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │ bind mount         │ bind mount                 │
│           ▼                    ▼                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Docker Container                    │   │
│  │  ┌─────────────────┐           ┌─────────────────┐  │   │
│  │  │  /app/src/      │           │  /app/          │  │   │
│  │  │  (mirrored)     │           │  (mirrored)     │  │   │
│  │  └─────────────────┘           └─────────────────┘  │   │
│  │  ┌─────────────────┐           ┌─────────────────┐  │   │
│  │  │ /app/node_modules│          │ site-packages/  │  │   │
│  │  │ (anonymous vol) │           │ (anonymous vol) │  │   │
│  │  │   (preserved!)  │           │   (preserved!)  │  │   │
│  │  └─────────────────┘           └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

**Container doesn't pick up changes:**
```bash
docker compose restart backend   # or frontend
```

**Stale node_modules or dependencies:**
```bash
docker compose down -v    # Removes anonymous volumes
docker compose up --build  # Rebuilds fresh
```

**Windows file watching issues:**
The override includes `WATCHPACK_POLLING=true` for better Windows compatibility.

**Permission errors on Linux:**
```bash
sudo chown -R $USER:$USER backend frontend
```

## Testing Hot-Reload

1. Start containers: `docker compose up`
2. Open http://localhost:3000
3. Edit `frontend/src/app/page.tsx` - change some text
4. Save and watch browser auto-refresh within ~1 second

For backend:
1. Edit `backend/app/main.py` - add a print statement
2. Save and watch logs show "Reloading..."
