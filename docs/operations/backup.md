# 🔄 Backup Operations

This document details comprehensive backup strategies and operations for your Kubernetes homelab environment, covering everything from configuration management to data protection.

## 🎯 Backup Philosophy

Homelab backup strategy follows the **3-2-1 principle**:
- **3** copies of important data
- **2** different storage media types
- **1** offsite backup

Additionally, we implement **Infrastructure as Code** principles where everything is declarative and version-controlled.

## 📦 Layered Backup Strategy

### 1. Configuration Backup (Git)

**What**: All Kubernetes manifests, Helm charts, and infrastructure code
**Why**: Enables complete environment recreation
**How**: Version control with Git repositories

```bash
# Daily configuration backup script
#!/bin/bash
set -euo pipefail

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
REPO_DIR="/home/johan/k8s-cluster-config"
BACKUP_DIR="/mnt/nas/backups/configs"

cd "$REPO_DIR"

# Create timestamped backup
echo "Creating configuration backup: $BACKUP_DATE"
git bundle create "$BACKUP_DIR/k8s-config-$BACKUP_DATE.bundle" --all

# Commit any uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    git add -A
    git commit -m "Automated backup: $BACKUP_DATE"
    git push origin main
fi

# Cleanup old bundles (keep last 30 days)
find "$BACKUP_DIR" -name "k8s-config-*.bundle" -mtime +30 -delete

echo "Configuration backup completed successfully"
```

### 2. Persistent Volume Backup (Longhorn)

**What**: Application data stored in persistent volumes
**Why**: Protects stateful application data
**How**: Automated Longhorn snapshots with retention policies

```yaml
# Longhorn recurring backup configuration
apiVersion: longhorn.io/v1beta1
kind: RecurringJob
metadata:
  name: daily-backup
  namespace: longhorn-system
spec:
  cron: "0 2 * * *"  # Daily at 2 AM
  task: "backup"
  groups:
  - "critical"
  - "important"
  retain: 14  # Keep 14 daily backups
  concurrency: 2
  labels:
    backup-type: "daily"
---
apiVersion: longhorn.io/v1beta1
kind: RecurringJob
metadata:
  name: weekly-backup
  namespace: longhorn-system
spec:
  cron: "0 3 * * 0"  # Weekly on Sunday at 3 AM
  task: "backup"
  groups:
  - "critical"
  retain: 8  # Keep 8 weekly backups
  concurrency: 1
  labels:
    backup-type: "weekly"
```

**Label your volumes for backup groups**:
```bash
# Label critical volumes
kubectl label pv pvc-monitoring-prometheus-server critical=true
kubectl label pv pvc-grafana-storage critical=true

# Label important volumes
kubectl label pv pvc-application-data important=true
```

### 3. Kubernetes Resource Backup (Velero)

**What**: Complete Kubernetes cluster state and resources
**Why**: Enables cluster-level disaster recovery
**How**: Velero with MinIO backend storage

```yaml
# Velero installation with MinIO backend
apiVersion: v1
kind: Secret
metadata:
  name: minio-credentials
  namespace: velero
type: Opaque
data:
  cloud: |
    [default]
    aws_access_key_id=minio-access-key
    aws_secret_access_key=minio-secret-key
---
apiVersion: velero.io/v1
kind: BackupStorageLocation
metadata:
  name: minio-backups
  namespace: velero
spec:
  provider: aws
  objectStorage:
    bucket: velero-backups
    prefix: homelab-cluster
  config:
    region: us-east-1
    s3ForcePathStyle: "true"
    s3Url: http://minio.storage.svc.cluster.local:9000
---
# Daily backup schedule
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
  namespace: velero
spec:
  schedule: "0 1 * * *"  # Daily at 1 AM
  template:
    ttl: 720h  # 30 days retention
    includeClusterResources: true
    storageLocation: minio-backups
    excludedNamespaces:
    - kube-system
    - velero
    - longhorn-system
```

## 🔧 Backup Automation Scripts

### Comprehensive Backup Script

```bash
#!/bin/bash
# homelab-backup.sh - Comprehensive backup automation

set -euo pipefail

# Configuration
LOG_FILE="/var/log/homelab-backup.log"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Notification function
notify() {
    local status="$1"
    local message="$2"
    
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🔄 Homelab Backup $status: $message\"}" \
        "$SLACK_WEBHOOK" || true
}

# Pre-backup health checks
health_check() {
    log "Starting pre-backup health checks..."
    
    # Check kubectl connectivity
    if ! kubectl cluster-info > /dev/null 2>&1; then
        log "ERROR: kubectl connectivity failed"
        notify "FAILED" "kubectl connectivity check failed"
        exit 1
    fi
    
    # Check disk space
    local disk_usage=$(df /mnt/nas | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 85 ]]; then
        log "WARNING: Disk usage is ${disk_usage}%"
        notify "WARNING" "Backup storage at ${disk_usage}% capacity"
    fi
    
    # Check Longhorn health
    local unhealthy_volumes=$(kubectl get volumes -n longhorn-system -o json | \
        jq -r '.items[] | select(.status.state != "attached" and .status.state != "detached") | .metadata.name' | wc -l)
    
    if [[ $unhealthy_volumes -gt 0 ]]; then
        log "WARNING: $unhealthy_volumes unhealthy Longhorn volumes detected"
        notify "WARNING" "$unhealthy_volumes unhealthy Longhorn volumes"
    fi
    
    log "Health checks completed"
}

# Git configuration backup
backup_configurations() {
    log "Starting configuration backup..."
    
    local config_dirs=(
        "/home/johan/k8s-cluster-config"
        "/home/johan/homelab-docs"
    )
    
    for dir in "${config_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            cd "$dir"
            local repo_name=$(basename "$dir")
            
            # Create bundle backup
            git bundle create "/mnt/nas/backups/configs/${repo_name}-${BACKUP_DATE}.bundle" --all
            
            # Commit and push any changes
            if [[ -n $(git status --porcelain) ]]; then
                git add -A
                git commit -m "Automated backup: $BACKUP_DATE" || true
                git push origin main || true
            fi
            
            log "Configuration backup completed for $repo_name"
        fi
    done
}

# Trigger Velero backup
trigger_velero_backup() {
    log "Triggering Velero backup..."
    
    local backup_name="manual-backup-$BACKUP_DATE"
    
    # Create backup
    kubectl create backup "$backup_name" \
        --storage-location minio-backups \
        --ttl 720h \
        --include-cluster-resources=true \
        --wait
    
    # Check backup status
    local backup_status=$(kubectl get backup "$backup_name" -o jsonpath='{.status.phase}')
    
    if [[ "$backup_status" == "Completed" ]]; then
        log "Velero backup completed successfully"
    else
        log "ERROR: Velero backup failed with status: $backup_status"
        notify "FAILED" "Velero backup failed: $backup_status"
        return 1
    fi
}

# Trigger Longhorn snapshots
trigger_longhorn_snapshots() {
    log "Triggering Longhorn snapshots..."
    
    # Get all PVs with backup labels
    local critical_pvs=$(kubectl get pv -l critical=true -o name)
    local important_pvs=$(kubectl get pv -l important=true -o name)
    
    for pv in $critical_pvs $important_pvs; do
        local pv_name=$(echo "$pv" | cut -d'/' -f2)
        log "Creating snapshot for $pv_name"
        
        # Trigger snapshot via Longhorn API
        curl -X POST "http://longhorn-frontend.longhorn-system.svc.cluster.local/v1/volumes/$pv_name?action=snapshotCreate" \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"manual-$BACKUP_DATE\"}" || true
    done
    
    log "Longhorn snapshots triggered"
}

# Database backups (if applicable)
backup_databases() {
    log "Starting database backups..."
    
    # PostgreSQL backup example
    if kubectl get pods -n database -l app=postgresql --no-headers | grep -q Running; then
        kubectl exec -n database postgresql-0 -- pg_dumpall -U postgres | \
            gzip > "/mnt/nas/backups/databases/postgresql-$BACKUP_DATE.sql.gz"
        log "PostgreSQL backup completed"
    fi
    
    # Redis backup example
    if kubectl get pods -n database -l app=redis --no-headers | grep -q Running; then
        kubectl exec -n database redis-0 -- redis-cli BGSAVE
        kubectl cp database/redis-0:/data/dump.rdb "/mnt/nas/backups/databases/redis-$BACKUP_DATE.rdb"
        log "Redis backup completed"
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Configuration bundles (keep 30 days)
    find /mnt/nas/backups/configs -name "*.bundle" -mtime +30 -delete
    
    # Database backups (keep 14 days)
    find /mnt/nas/backups/databases -name "*.sql.gz" -mtime +14 -delete
    find /mnt/nas/backups/databases -name "*.rdb" -mtime +14 -delete
    
    # Clean up old Velero backups
    kubectl get backups -o json | jq -r '.items[] | select(.status.expiration < now) | .metadata.name' | \
        xargs -r kubectl delete backup
    
    log "Cleanup completed"
}

# Main execution
main() {
    log "=== Starting homelab backup process ==="
    notify "STARTED" "Backup process initiated"
    
    local start_time=$(date +%s)
    
    # Execute backup steps
    health_check
    backup_configurations
    trigger_velero_backup
    trigger_longhorn_snapshots
    backup_databases
    cleanup_old_backups
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "=== Backup process completed in ${duration}s ==="
    notify "COMPLETED" "Backup finished successfully in ${duration}s"
}

# Run main function
main "$@"
```

## 🔄 Recovery Procedures

### 1. Configuration Recovery

**Scenario**: Need to rebuild cluster from scratch

```bash
# Clone configuration repository
git clone https://github.com/your-org/k8s-cluster-config.git
cd k8s-cluster-config

# Apply all configurations in order
kubectl apply -k infrastructure/traefik/
kubectl apply -k infrastructure/longhorn/
kubectl apply -k infrastructure/monitoring/
kubectl apply -k applications/

# Verify deployment
kubectl get pods --all-namespaces
```

### 2. Volume Recovery from Longhorn

**Scenario**: Restore specific application data

```bash
# List available backups
kubectl get backups -n longhorn-system

# Restore from backup
kubectl apply -f - <<EOF
apiVersion: longhorn.io/v1beta1
kind: Volume
metadata:
  name: restored-volume
  namespace: longhorn-system
spec:
  fromBackup: "s3://longhorn-backups/backups/backup-xyz"
  size: "10Gi"
EOF

# Create PVC for restored volume
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-data
  namespace: applications
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  volumeName: restored-volume
EOF
```

### 3. Full Cluster Recovery with Velero

**Scenario**: Complete cluster disaster recovery

```bash
# Install Velero on new cluster
velero install \
    --provider aws \
    --plugins velero/velero-plugin-for-aws:v1.5.0 \
    --bucket velero-backups \
    --secret-file ./minio-credentials \
    --backup-location-config region=us-east-1,s3ForcePathStyle="true",s3Url=http://minio-endpoint

# List available backups
velero backup get

# Restore from specific backup
velero restore create \
    --from-backup daily-backup-20240115-010000 \
    --wait

# Monitor restore progress
velero restore describe restore-name
velero restore logs restore-name
```

## ✅ Backup Validation

### Automated Testing Script

```bash
#!/bin/bash
# backup-validation.sh - Test backup integrity

set -euo pipefail

# Test configuration backup integrity
test_config_backups() {
    echo "Testing configuration backup integrity..."
    
    local latest_bundle=$(ls -t /mnt/nas/backups/configs/*.bundle | head -1)
    
    # Test bundle integrity
    if git bundle verify "$latest_bundle" > /dev/null 2>&1; then
        echo "✅ Configuration backup integrity verified"
    else
        echo "❌ Configuration backup integrity check failed"
        return 1
    fi
}

# Test Velero backup status
test_velero_backups() {
    echo "Testing Velero backup status..."
    
    local failed_backups=$(kubectl get backups -o json | \
        jq -r '.items[] | select(.status.phase == "Failed") | .metadata.name' | wc -l)
    
    if [[ $failed_backups -eq 0 ]]; then
        echo "✅ All Velero backups completed successfully"
    else
        echo "❌ $failed_backups Velero backups failed"
        return 1
    fi
}

# Test Longhorn snapshot status
test_longhorn_snapshots() {
    echo "Testing Longhorn snapshot status..."
    
    local failed_snapshots=$(kubectl get snapshots -n longhorn-system -o json | \
        jq -r '.items[] | select(.status.readyToUse == false) | .metadata.name' | wc -l)
    
    if [[ $failed_snapshots -eq 0 ]]; then
        echo "✅ All Longhorn snapshots are healthy"
    else
        echo "❌ $failed_snapshots Longhorn snapshots are unhealthy"
        return 1
    fi
}

# Test restore capability
test_restore_capability() {
    echo "Testing restore capability..."
    
    # Create test namespace
    kubectl create namespace backup-test --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy test application
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backup-test
  namespace: backup-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backup-test
  template:
    metadata:
      labels:
        app: backup-test
    spec:
      containers:
      - name: test
        image: busybox
        command: ['sleep', '3600']
        volumeMounts:
        - name: test-data
          mountPath: /data
      volumes:
      - name: test-data
        persistentVolumeClaim:
          claimName: test-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
  namespace: backup-test
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

    # Wait for pod to be ready
    kubectl wait --for=condition=ready pod -l app=backup-test -n backup-test --timeout=60s
    
    # Write test data
    kubectl exec -n backup-test deployment/backup-test -- sh -c 'echo "test-data-$(date)" > /data/test.txt'
    
    # Create backup
    velero backup create backup-test --include-namespaces backup-test --wait
    
    # Delete namespace
    kubectl delete namespace backup-test
    
    # Restore from backup
    velero restore create restore-test --from-backup backup-test --wait
    
    # Verify data
    kubectl wait --for=condition=ready pod -l app=backup-test -n backup-test --timeout=60s
    local restored_data=$(kubectl exec -n backup-test deployment/backup-test -- cat /data/test.txt)
    
    if [[ "$restored_data" == test-data-* ]]; then
        echo "✅ Restore capability verified"
    else
        echo "❌ Restore capability test failed"
        return 1
    fi
    
    # Cleanup
    kubectl delete namespace backup-test
    velero backup delete backup-test --confirm
    velero restore delete restore-test --confirm
}

# Main validation
main() {
    echo "=== Starting backup validation ==="
    
    test_config_backups
    test_velero_backups
    test_longhorn_snapshots
    test_restore_capability
    
    echo "=== Backup validation completed successfully ==="
}

main "$@"
```

## 📅 Backup Schedule

### Recommended Backup Frequency

| Component | Frequency | Retention | Method |
|-----------|-----------|-----------|--------|
| **Git Configs** | On every change | 1 year | Git push + Bundle |
| **Application Data** | Daily | 30 days | Longhorn snapshots |
| **Cluster State** | Daily | 30 days | Velero |
| **Database Dumps** | Daily | 14 days | pg_dump/redis BGSAVE |
| **Full System** | Weekly | 8 weeks | Complete restore test |

### Cron Schedule Setup

```bash
# Add to crontab (crontab -e)

# Daily backup at 2 AM
0 2 * * * /home/johan/scripts/homelab-backup.sh

# Weekly validation on Sundays at 3 AM
0 3 * * 0 /home/johan/scripts/backup-validation.sh

# Monthly full restore test on first Saturday at 4 AM
0 4 1-7 * 6 /home/johan/scripts/full-restore-test.sh
```

## 🚨 Monitoring and Alerting

### Backup Monitoring Dashboard

```yaml
# Prometheus alert rules for backup monitoring
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: backup-alerts
  namespace: monitoring
spec:
  groups:
  - name: backup-health
    rules:
    - alert: VeleroBackupFailure
      expr: increase(velero_backup_failure_total[24h]) > 0
      for: 0m
      labels:
        severity: critical
      annotations:
        summary: "Velero backup failed"
        description: "Velero backup has failed in the last 24 hours"
    
    - alert: LonghornSnapshotOld
      expr: time() - longhorn_snapshot_created_timestamp > 86400 * 2  # 2 days
      for: 1h
      labels:
        severity: warning
      annotations:
        summary: "Longhorn snapshot is old"
        description: "No recent Longhorn snapshots for volume {{ $labels.volume }}"
    
    - alert: BackupStorageFull
      expr: (backup_storage_used_bytes / backup_storage_total_bytes) > 0.9
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Backup storage almost full"
        description: "Backup storage is {{ $value | humanizePercentage }} full"
```

This comprehensive backup strategy ensures your homelab data and configurations are protected through multiple layers of redundancy, with automated processes and validation to maintain backup integrity.
