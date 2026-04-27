#!/bin/bash
# Run this on your production server at /opt/emoratest/

echo "=== Step 1: Check current .env file ==="
grep NEXT_PUBLIC_API_URL .env || echo "NEXT_PUBLIC_API_URL NOT FOUND in .env"

echo ""
echo "=== Step 2: Add NEXT_PUBLIC_API_URL if missing ==="
grep -q "NEXT_PUBLIC_API_URL" .env || echo "NEXT_PUBLIC_API_URL=https://emoratest.com" >> .env

echo ""
echo "=== Step 3: Verify .env after ==="
grep NEXT_PUBLIC_API_URL .env

echo ""
echo "=== Step 4: Stop frontend ==="
docker-compose -f docker-compose.prod.yml stop frontend

echo ""
echo "=== Step 5: Remove old frontend image (force rebuild) ==="
docker-compose -f docker-compose.prod.yml rm -f frontend
docker rmi emoratest-frontend 2>/dev/null || echo "Image removed or doesn't exist"

echo ""
echo "=== Step 6: Rebuild frontend with env var ==="
docker-compose -f docker-compose.prod.yml build --no-cache frontend

echo ""
echo "=== Step 7: Start frontend ==="
docker-compose -f docker-compose.prod.yml up -d frontend

echo ""
echo "=== Step 8: Verify container is running ==="
docker-compose -f docker-compose.prod.yml ps frontend

echo ""
echo "=== Step 9: Check container logs for build env ==="
docker-compose -f docker-compose.prod.yml logs frontend | grep -i "NEXT_PUBLIC" || echo "No NEXT_PUBLIC in logs"

echo ""
echo "=== DONE! Clear your browser cache and try again ==="
