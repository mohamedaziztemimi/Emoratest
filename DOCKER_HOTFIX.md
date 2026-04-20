# Docker Hot Reload - Quick Fix

## If hot reload isn't working, run these commands in order:

### 1. Stop and clean everything
```bash
docker compose down -v
```

### 2. Rebuild from scratch (IMPORTANT - use --build and --force-recreate)
```bash
docker compose up --build --force-recreate
```

### 3. Check if hot reload is working
- Edit any file in `frontend/src/` or `backend/app/`
- Check logs: `docker compose logs -f backend frontend`
- You should see "Reloading..." or similar messages

## If still not working on Windows:

### Add this to docker-compose.override.yml frontend environment:
```yaml
- WATCHPACK_POLLING=true
- CHOKIDAR_USEPOLLING=true
- CHOKIDAR_INTERVAL=1000
```

### For backend, ensure the Dockerfile has:
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level=debug"]
```

## Common Issues:

| Issue | Fix |
|-------|-----|
| Changes not detected | Use polling env vars (Windows) |
| node_modules gets overwritten | Anonymous volume should protect it |
| Backend not restarting | Check `--reload` flag in CMD |
| Need to rebuild after dependency change | `docker compose up --build` |

## Test it works:
1. `docker compose up --build`
2. Edit `frontend/src/app/page.tsx` - change some text
3. Browser should auto-refresh within 2-3 seconds
