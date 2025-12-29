# PROMETHEUS v2.0 — Production Deployment Guide

## Phase 2 Execution: Trust-Engine-First AI Orchestration

### 🎯 Deployment Overview

This guide deploys **PROMETHEUS v2.0** — an auditable, evidence-gated AI orchestration engine built for high-stakes workflows.

**Key Guarantees:**
- ✅ Every AI claim has proof. Hallucinations rejected at runtime.
- ✅ Full execution lineage for compliance audits
- ✅ Guardian agents enforce safety gates
- ✅ MCP-first design (extensible tool ecosystem)

---

## Pre-Deployment Checklist

### System Requirements
```
✅ Python 3.8+
✅ 4+ CPU cores (8+ for production)
✅ 16GB+ RAM (32GB recommended)
✅ 100GB+ SSD storage
✅ Docker 20.10+
✅ PostgreSQL 13+ (or managed RDS)
✅ Redis 6+ (for caching & state)
```

### Credential Setup
```bash
# Create .env from template
cp .env.example .env

# Required keys:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-anthropic-...
GUMROAD_API_KEY=...
ETSY_API_KEY=...
JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
ENCRYPTION_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
```

### Verification
```bash
# Run checkpoint tests
python WEEK_2_STATE_MACHINE.py --verify

# Output should show:
✅ State machine verified
✅ Checkpoint system operational
✅ Evidence gates armed
✅ All systems operational
```

---

## Docker Deployment (Recommended for Local/Dev)

### Quick Start
```bash
# Build image
docker build -t prometheus:v2.0 -f Dockerfile .

# Run container
docker run -d \
  --name prometheus-v2 \
  --env-file .env \
  -p 8000:8000 \
  -p 9090:9090 \
  -v prometheus-data:/data \
  prometheus:v2.0

# Verify deployment
curl -s http://localhost:8000/health | jq .
```

### Docker Compose (Recommended)
```bash
# Full stack: app + PostgreSQL + Redis + Prometheus
docker-compose -f docker-compose.prod.yml up -d

# Logs
docker-compose -f docker-compose.prod.yml logs -f app

# Verify services
docker-compose -f docker-compose.prod.yml ps
```

---

## Kubernetes Deployment (Production)

### Prerequisites
```bash
# Verify cluster access
kubectl cluster-info
kubectl get nodes

# Create namespace
kubectl create namespace prometheus-prod
kubectl config set-context --current --namespace=prometheus-prod
```

### Deploy
```bash
# Create secrets from .env
kubectl create secret generic prometheus-secrets --from-env-file=.env

# Apply manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get pods
kubectl get svc
kubectl logs -f deployment/prometheus-app
```

### Health Checks
```bash
# Port forward to local
kubectl port-forward svc/prometheus-app 8000:8000

# Test health
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

---

## AWS Deployment (ECS + RDS)

### Infrastructure Setup
```bash
# Create RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier prometheus-prod-db \
  --db-instance-class db.t3.large \
  --engine postgres \
  --allocated-storage 100

# Create ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id prometheus-cache \
  --cache-node-type cache.t3.medium \
  --engine redis

# Push image to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.REGION.amazonaws.com
docker tag prometheus:v2.0 ACCOUNT.dkr.ecr.REGION.amazonaws.com/prometheus:v2.0
docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/prometheus:v2.0
```

### ECS Task Definition
```json
{
  "family": "prometheus-v2",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "prometheus",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/prometheus:v2.0",
      "portMappings": [{"containerPort": 8000}],
      "environment": [{"name": "ENVIRONMENT", "value": "production"}],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/prometheus-v2",
          "awslogs-region": "REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Deploy to ECS
```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster prometheus-prod \
  --service-name prometheus-v2 \
  --task-definition prometheus-v2 \
  --desired-count 2 \
  --launch-type FARGATE

# Monitor
aws ecs describe-services --cluster prometheus-prod --services prometheus-v2
```

---

## Monitoring & Observability

### Prometheus Metrics
```bash
# Metrics endpoint
curl http://localhost:9090/metrics

# Key metrics:
prometheus_evidence_gates_rejected_total
prometheus_execution_lineage_depth
prometheus_checkpoint_success_rate
prometheus_guardian_decisions_per_second
```

### Datadog Integration
```bash
# Enable in .env
DATADOG_API_KEY=dd_...

# Automated dashboards:
- Execution Flow Lineage
- Evidence Gate Decisions
- Checkpoint Verification Rate
- Guardian Agent Performance
- Error & Hallucination Detection
```

### Sentry Error Tracking
```bash
SENTRY_DSN=https://...

# Automatic error reporting:
- Hallucinations detected & rejected
- Gate failures
- Evidence validation errors
- Checkpoint corruption
```

---

## Security Configuration

### Network Security
```bash
# Enable TLS
SSL_CERT_FILE=/etc/ssl/certs/prometheus.crt
SSL_KEY_FILE=/etc/ssl/private/prometheus.key

# Firewall rules (UFW example)
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw allow from 10.0.0.0/8 to any port 9090
```

### Data Encryption
```bash
# At-rest encryption
ENCRYPTION_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Database encryption
aws rds modify-db-instance \
  --db-instance-identifier prometheus-prod-db \
  --storage-encrypted
```

### PII Detection
```yaml
# Enabled by default
PII_DETECTION_ENABLED: true
AUDIT_LOGGING: true
CONTENT_POLICY_STRICT: true
```

---

## Performance Optimization

### Caching Strategy
```bash
# Redis configuration
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# Auto-caching:
- Evidence verification results (1h)
- Checkpoint manifests (6h)
- Guardian decision patterns (24h)
```

### Database Optimization
```sql
-- Create indexes
CREATE INDEX idx_execution_lineage ON executions(lineage_depth);
CREATE INDEX idx_evidence_gates ON evidence(rejection_reason);
CREATE INDEX idx_checkpoint_state ON checkpoints(state_hash);

-- Vacuum & analyze
VACUUM ANALYZE;
```

### Worker Configuration
```bash
# Optimal settings
WORKER_PROCESSES=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
WORKER_TIMEOUT=30
KEEPALIVE_TIMEOUT=2
```

---

## Backup & Recovery

### Automated Backups
```bash
# PostgreSQL backups (daily)
pg_dump prometheus_prod | gzip > backups/db_$(date +%Y%m%d).sql.gz

# Redis snapshots
redis-cli BGSAVE

# Checkpoint files
tar -czf backups/checkpoints_$(date +%Y%m%d).tar.gz ./checkpoints/
```

### Recovery Procedure
```bash
# Restore database
gzip -dc backups/db_20250101.sql.gz | psql prometheus_prod

# Restore Redis state
redis-cli --rdb backups/dump.rdb

# Restore checkpoints
tar -xzf backups/checkpoints_20250101.tar.gz

# Verify integrity
python WEEK_2_STATE_MACHINE.py --verify
```

---

## Troubleshooting

### Common Issues

#### ❌ Evidence Gates Rejecting Valid Claims
```bash
# Check gate configuration
curl http://localhost:8000/debug/gates

# Verify evidence repository
curl http://localhost:8000/debug/evidence-sources

# Increase gate threshold temporarily
echo 'EVIDENCE_THRESHOLD=0.8' >> .env
docker-compose restart app
```

#### ❌ Checkpoint Corruption
```bash
# Verify checkpoints
python WEEK_2_STATE_MACHINE.py --verify

# Rebuild from valid checkpoint
python -c "from src.checkpoint_manager import CheckpointManager; CheckpointManager.rebuild_from_backup()"
```

#### ❌ High Latency
```bash
# Check resource usage
docker stats

# Scale horizontally
docker-compose up -d --scale app=3

# Monitor metrics
curl http://localhost:9090/metrics | grep latency
```

---

## Support & Escalation

**Issues?**
- 📧 Email: DouglasMitchell@HoustonOilAirs.org
- 🐛 GitHub Issues: https://github.com/Senpai-Sama7/prometheus-stack/issues
- 📊 Status Dashboard: http://localhost:8000/status

---

**Deployment Status: ✅ READY FOR PRODUCTION**

All systems tested. Evidence gates armed. Checkpoints verified. Ship it. 🚀