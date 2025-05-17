#!/usr/bin/env bash
set -euo pipefail

SHA=$(git rev-parse HEAD)
STAGING_DIR="deployments/$SHA"
mkdir -p "$STAGING_DIR"
LOG_FILE="$STAGING_DIR/deployment.log"

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

log "Starting staging deployment for commit $SHA"

COMPONENTS=(backend frontend worker migrations)
REGISTRY="internal.registry"

for COMP in "${COMPONENTS[@]}"; do
    IMAGE="$REGISTRY/arabic-llm-$COMP:$SHA"
    log "Building image $IMAGE"
    docker build -t "$IMAGE" "$COMP"
    log "Pushing image $IMAGE"
    docker push "$IMAGE"
done

COMPOSE_PROJECT_NAME="staging-$SHA"
export COMPOSE_PROJECT_NAME
log "Launching environment $COMPOSE_PROJECT_NAME"

docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d

sleep 10

log "Applying database migrations"
docker-compose exec migrations alembic upgrade head

log "Running automated tests"
pytest &> "$STAGING_DIR/test_results.log"
log "Tests finished with exit code $?"

HEALTH_OK=true
for URL in "http://localhost:8000/healthz" "http://localhost:8000/api/v1/documents"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
    log "Health check $URL -> $STATUS"
    if [ "$STATUS" != "200" ]; then
        HEALTH_OK=false
    fi
done

if [ "$HEALTH_OK" = false ]; then
    log "Health checks failed"
    docker-compose down
    exit 1
fi

log "Seeding demo data"
docker-compose exec backend python app/scripts/seed_demo_data.py

STAGING_URL="https://staging-$SHA.example.com"
log "Exposing staging environment at $STAGING_URL"

cat <<SUMMARY > "$STAGING_DIR/summary.md"
# Staging Deployment Summary

- Commit SHA: $SHA
- Images:
$(for COMP in "${COMPONENTS[@]}"; do echo "  - $COMP: $REGISTRY/arabic-llm-$COMP:$SHA"; done)
- Migrations: successful
- Test suite: see test_results.log
- Health checks: passed
- Staging URL: $STAGING_URL (basic auth qa/qa123)
SUMMARY

log "Deployment completed"
