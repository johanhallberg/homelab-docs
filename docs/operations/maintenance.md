# 🔧 Maintenance Operations

This document covers comprehensive maintenance practices for your Kubernetes homelab environment, ensuring optimal performance, security, and reliability through proactive management.

## 🎯 Maintenance Philosophy

Maintenance in a homelab environment should be:
- **Proactive**: Prevent issues before they occur
- **Automated**: Reduce manual intervention
- **Monitored**: Track system health continuously
- **Documented**: Record all changes and procedures
- **Tested**: Validate changes in non-production first

## 🔄 Regular Maintenance Tasks

### Daily Maintenance (Automated)

#### 1. Health Checks

```bash
#!/bin/bash
# daily-health-check.sh - Automated daily system health verification

set -euo pipefail

LOG_FILE="/var/log/daily-health-check.log"
ALERT_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Alert function
alert() {
    local severity="$1"
    local message="$2"
    
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$severity: $message\"}" \
        "$ALERT_WEBHOOK" || true
    
    log "ALERT [$severity]: $message"
}

# Check cluster connectivity
check_cluster_connectivity() {
    log "Checking cluster connectivity..."
    
    if ! kubectl cluster-info > /dev/null 2>&1; then
        alert "CRITICAL" "Kubernetes cluster is unreachable"
        return 1
    fi
    
    local ready_nodes=$(kubectl get nodes --no-headers | grep " Ready " | wc -l)
    local total_nodes=$(kubectl get nodes --no-headers | wc -l)
    
    if [[ $ready_nodes -ne $total_nodes ]]; then
        alert "WARNING" "$((total_nodes - ready_nodes)) nodes are not ready"
    else
        log "All $total_nodes nodes are ready"
    fi
}

# Check pod health
check_pod_health() {
    log "Checking pod health across all namespaces..."
    
    # Check for pods in error states
    local failed_pods=$(kubectl get pods --all-namespaces --field-selector=status.phase=Failed --no-headers | wc -l)
    local pending_pods=$(kubectl get pods --all-namespaces --field-selector=status.phase=Pending --no-headers | wc -l)
    
    if [[ $failed_pods -gt 0 ]]; then
        alert "WARNING" "$failed_pods pods are in Failed state"
        kubectl get pods --all-namespaces --field-selector=status.phase=Failed --no-headers | head -5 | while read line; do
            log "Failed Pod: $line"
        done
    fi
    
    if [[ $pending_pods -gt 0 ]]; then
        alert "WARNING" "$pending_pods pods are in Pending state"
        kubectl get pods --all-namespaces --field-selector=status.phase=Pending --no-headers | head -5 | while read line; do
            log "Pending Pod: $line"
        done
    fi
    
    # Check pods with high restart counts
    kubectl get pods --all-namespaces --no-headers | awk '$5 > 5 {print}' | while read line; do
        alert "WARNING" "High restart count pod: $line"
    done
    
    log "Pod health check completed"
}

# Check storage health
check_storage_health() {
    log "Checking storage health..."
    
    # Check PVC status
    local pending_pvcs=$(kubectl get pvc --all-namespaces --no-headers | grep -c Pending || true)
    if [[ $pending_pvcs -gt 0 ]]; then
        alert "WARNING" "$pending_pvcs PVCs are in Pending state"
    fi
    
    # Check Longhorn volume health
    if kubectl get volumes -n longhorn-system > /dev/null 2>&1; then
        local degraded_volumes=$(kubectl get volumes -n longhorn-system -o json | \
            jq -r '.items[] | select(.status.robustness == "degraded") | .metadata.name' | wc -l)
        
        if [[ $degraded_volumes -gt 0 ]]; then
            alert "CRITICAL" "$degraded_volumes Longhorn volumes are degraded"
        fi
        
        # Check storage usage
        local storage_usage=$(kubectl get nodes -o json | \
            jq -r '.items[] | .status.allocatable."ephemeral-storage"' | \
            numfmt --from=iec | awk '{sum+=$1} END {print sum}')
        
        log "Total allocatable storage: $(echo $storage_usage | numfmt --to=iec)"
    fi
    
    log "Storage health check completed"
}

# Check resource utilization
check_resource_utilization() {
    log "Checking resource utilization..."
    
    # CPU and Memory usage per node
    kubectl top nodes --no-headers | while read node cpu_pct cpu_cores mem_pct mem_gb; do
        cpu_usage=${cpu_pct%\%}
        mem_usage=${mem_pct%\%}
        
        if [[ $cpu_usage -gt 80 ]]; then
            alert "WARNING" "Node $node CPU usage is ${cpu_usage}%"
        fi
        
        if [[ $mem_usage -gt 80 ]]; then
            alert "WARNING" "Node $node memory usage is ${mem_usage}%"
        fi
        
        log "Node $node: CPU ${cpu_usage}%, Memory ${mem_usage}%"
    done
    
    # Check for resource-constrained pods
    kubectl get pods --all-namespaces -o json | \
        jq -r '.items[] | select(.status.containerStatuses[]?.state.waiting?.reason == "CreateContainerConfigError" or .status.containerStatuses[]?.state.waiting?.reason == "ImagePullBackOff") | "\(.metadata.namespace)/\(.metadata.name): \(.status.containerStatuses[0].state.waiting.reason)"' | \
        while read pod_info; do
            alert "WARNING" "Resource issue: $pod_info"
        done
    
    log "Resource utilization check completed"
}

# Check certificate expiration
check_certificate_expiration() {
    log "Checking certificate expiration..."
    
    # Check TLS secrets for expiration
    kubectl get secrets --all-namespaces -o json | \
        jq -r '.items[] | select(.type == "kubernetes.io/tls") | "\(.metadata.namespace) \(.metadata.name) \(.data."tls.crt")"' | \
        while read namespace secret cert_data; do
            if [[ -n "$cert_data" ]]; then
                expiry_date=$(echo "$cert_data" | base64 -d | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
                expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null || echo "0")
                current_epoch=$(date +%s)
                days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
                
                if [[ $days_until_expiry -lt 30 ]]; then
                    if [[ $days_until_expiry -lt 7 ]]; then
                        alert "CRITICAL" "Certificate $namespace/$secret expires in $days_until_expiry days"
                    else
                        alert "WARNING" "Certificate $namespace/$secret expires in $days_until_expiry days"
                    fi
                fi
            fi
        done
    
    log "Certificate expiration check completed"
}

# Main execution
main() {
    log "=== Starting daily health check ==="
    
    check_cluster_connectivity
    check_pod_health
    check_storage_health
    check_resource_utilization
    check_certificate_expiration
    
    log "=== Daily health check completed ==="
}

main "$@"
```

#### 2. Log Rotation and Cleanup

```bash
#!/bin/bash
# daily-cleanup.sh - Clean up logs and temporary files

set -euo pipefail

# Clean up container logs older than 7 days
find /var/lib/docker/containers -name "*.log" -mtime +7 -delete 2>/dev/null || true

# Clean up old Kubernetes logs
find /var/log/pods -type f -mtime +7 -delete 2>/dev/null || true

# Clean up old journal logs (keep last 7 days)
journalctl --vacuum-time=7d

# Clean up old backup validation logs
find /var/log -name "*backup*" -mtime +30 -delete 2>/dev/null || true

# Clean up old image layers
docker system prune -f --filter "until=168h" # 7 days

# Clean up unused Longhorn snapshots (beyond retention policy)
kubectl get snapshots -n longhorn-system -o json | \
    jq -r '.items[] | select(.metadata.creationTimestamp | fromdateiso8601 < (now - 86400 * 30)) | .metadata.name' | \
    head -10 | \
    xargs -r -I {} kubectl delete snapshot {} -n longhorn-system

echo "Daily cleanup completed at $(date)"
```

### Weekly Maintenance (Semi-Automated)

#### 1. Security Updates and Patching

```bash
#!/bin/bash
# weekly-security-updates.sh - Apply security updates

set -euo pipefail

LOG_FILE="/var/log/weekly-maintenance.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Update container images
update_container_images() {
    log "Checking for container image updates..."
    
    # Get all container images in use
    kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}' | \
        sort -u | \
        while read image; do
            if [[ "$image" != *":latest" && "$image" != *"@sha256:"* ]]; then
                log "Checking updates for image: $image"
                
                # Pull latest version
                docker pull "$image" 2>/dev/null || {
                    log "Failed to pull $image"
                    continue
                }
                
                # Check if there's a newer version
                current_digest=$(docker inspect --format='{{index .RepoDigests 0}}' "$image" 2>/dev/null || echo "")
                latest_digest=$(docker inspect --format='{{index .RepoDigests 0}}' "${image%:*}:latest" 2>/dev/null || echo "")
                
                if [[ "$current_digest" != "$latest_digest" && -n "$latest_digest" ]]; then
                    log "Update available for $image"
                    echo "$image" >> /tmp/images-to-update.txt
                fi
            fi
        done
    
    if [[ -f /tmp/images-to-update.txt ]]; then
        log "Images with updates available:"
        cat /tmp/images-to-update.txt | tee -a "$LOG_FILE"
        log "Consider updating these images in your deployments"
    else
        log "All container images are up to date"
    fi
    
    rm -f /tmp/images-to-update.txt
}

# Update system packages
update_system_packages() {
    log "Updating system packages..."
    
    # Update package list
    apt-get update -qq
    
    # Check for security updates
    security_updates=$(apt list --upgradable 2>/dev/null | grep -c security || echo "0")
    
    if [[ $security_updates -gt 0 ]]; then
        log "Applying $security_updates security updates..."
        
        # Apply only security updates
        unattended-upgrade -d || {
            log "Unattended upgrade failed, applying manual security updates"
            apt-get upgrade -y
        }
        
        # Check if reboot is required
        if [[ -f /var/run/reboot-required ]]; then
            log "Reboot required after security updates"
            # Schedule reboot for next maintenance window
            echo "$(date): Reboot required after security updates" >> /var/log/reboot-required.log
        fi
    else
        log "No security updates available"
    fi
}

# Update Kubernetes components
update_kubernetes_components() {
    log "Checking Kubernetes component versions..."
    
    # Check kubectl version
    local kubectl_version=$(kubectl version --client -o json | jq -r '.clientVersion.gitVersion')
    local server_version=$(kubectl version -o json | jq -r '.serverVersion.gitVersion')
    
    log "kubectl version: $kubectl_version"
    log "API server version: $server_version"
    
    # Check for available kubeadm updates
    if command -v kubeadm > /dev/null; then
        local current_kubeadm=$(kubeadm version -o short)
        log "Current kubeadm version: $current_kubeadm"
        
        # Check available versions
        apt-cache madison kubeadm | head -5 | while read line; do
            log "Available kubeadm: $line"
        done
    fi
    
    log "Review and plan Kubernetes component updates during next maintenance window"
}

main() {
    log "=== Starting weekly security updates ==="
    
    update_system_packages
    update_container_images
    update_kubernetes_components
    
    log "=== Weekly security updates completed ==="
}

main "$@"
```

#### 2. Performance Optimization

```bash
#!/bin/bash
# weekly-performance-optimization.sh - Optimize system performance

set -euo pipefail

LOG_FILE="/var/log/performance-optimization.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Optimize container resource allocations
optimize_resource_allocations() {
    log "Analyzing resource usage patterns..."
    
    # Generate resource usage report
    kubectl top pods --all-namespaces --sort-by=cpu --no-headers | head -20 | while read namespace pod cpu memory; do
        # Get resource requests and limits
        requests_cpu=$(kubectl get pod "$pod" -n "$namespace" -o jsonpath='{.spec.containers[0].resources.requests.cpu}' 2>/dev/null || echo "none")
        limits_cpu=$(kubectl get pod "$pod" -n "$namespace" -o jsonpath='{.spec.containers[0].resources.limits.cpu}' 2>/dev/null || echo "none")
        requests_memory=$(kubectl get pod "$pod" -n "$namespace" -o jsonpath='{.spec.containers[0].resources.requests.memory}' 2>/dev/null || echo "none")
        limits_memory=$(kubectl get pod "$pod" -n "$namespace" -o jsonpath='{.spec.containers[0].resources.limits.memory}' 2>/dev/null || echo "none")
        
        log "High CPU pod: $namespace/$pod - Usage: $cpu, Requests: $requests_cpu, Limits: $limits_cpu"
        
        # Check if pod is over-provisioned
        if [[ "$requests_cpu" != "none" ]]; then
            # Convert to millicores for comparison
            usage_mc=$(echo "$cpu" | sed 's/m$//' | sed 's/[^0-9]//g')
            request_mc=$(echo "$requests_cpu" | sed 's/m$//' | sed 's/[^0-9]//g')
            
            if [[ -n "$usage_mc" && -n "$request_mc" && $usage_mc -lt $((request_mc / 2)) ]]; then
                log "RECOMMENDATION: Pod $namespace/$pod may be over-provisioned (using $usage_mc m, requested $request_mc m)"
            fi
        fi
    done
    
    # Check for pods without resource limits
    kubectl get pods --all-namespaces -o json | \
        jq -r '.items[] | select(.spec.containers[0].resources.limits == null) | "\(.metadata.namespace)/\(.metadata.name)"' | \
        head -10 | \
        while read pod_path; do
            log "RECOMMENDATION: Pod $pod_path has no resource limits set"
        done
}

# Optimize storage performance
optimize_storage() {
    log "Optimizing storage performance..."
    
    # Check for storage fragmentation in Longhorn
    if kubectl get volumes -n longhorn-system > /dev/null 2>&1; then
        kubectl get volumes -n longhorn-system -o json | \
            jq -r '.items[] | select(.status.actualSize > (.status.size * 0.8)) | .metadata.name' | \
            while read volume; do
                log "RECOMMENDATION: Volume $volume is highly fragmented (consider defragmentation)"
            done
    fi
    
    # Check for unused PVCs
    kubectl get pvc --all-namespaces -o json | \
        jq -r '.items[] | select(.status.phase == "Bound") | "\(.metadata.namespace) \(.metadata.name)"' | \
        while read namespace pvc; do
            # Check if PVC is actually used by any pod
            pod_count=$(kubectl get pods -n "$namespace" -o json | \
                jq -r --arg pvc "$pvc" '.items[] | select(.spec.volumes[]?.persistentVolumeClaim.claimName == $pvc) | .metadata.name' | wc -l)
            
            if [[ $pod_count -eq 0 ]]; then
                log "WARNING: PVC $namespace/$pvc appears to be unused"
            fi
        done
    
    # Clean up old snapshots beyond retention
    kubectl get snapshots -n longhorn-system -o json | \
        jq -r '.items[] | select(.metadata.creationTimestamp | fromdateiso8601 < (now - 86400 * 7)) | .metadata.name' | \
        head -5 | \
        while read snapshot; do
            log "Cleaning up old snapshot: $snapshot"
            kubectl delete snapshot "$snapshot" -n longhorn-system
        done
}

# Network optimization
optimize_network() {
    log "Checking network optimization opportunities..."
    
    # Check for services without proper selectors
    kubectl get svc --all-namespaces -o json | \
        jq -r '.items[] | select(.spec.selector == null and .spec.type != "ExternalName") | "\(.metadata.namespace)/\(.metadata.name)"' | \
        while read svc; do
            log "WARNING: Service $svc has no selector (may be misconfigured)"
        done
    
    # Check for unused services
    kubectl get svc --all-namespaces -o json | \
        jq -r '.items[] | select(.spec.type == "ClusterIP" and .spec.selector != null) | "\(.metadata.namespace) \(.metadata.name) \(.spec.selector | to_entries[] | "\(.key)=\(.value)")"' | \
        while read namespace svc selector; do
            pod_count=$(kubectl get pods -n "$namespace" -l "$selector" --no-headers 2>/dev/null | wc -l)
            if [[ $pod_count -eq 0 ]]; then
                log "WARNING: Service $namespace/$svc has no backing pods"
            fi
        done
}

main() {
    log "=== Starting weekly performance optimization ==="
    
    optimize_resource_allocations
    optimize_storage
    optimize_network
    
    log "=== Weekly performance optimization completed ==="
}

main "$@"
```

### Monthly Maintenance (Manual)

#### 1. Capacity Planning Review

```bash
#!/bin/bash
# monthly-capacity-review.sh - Generate capacity planning report

set -euo pipefail

REPORT_FILE="/var/log/capacity-report-$(date +%Y%m).md"

# Generate comprehensive capacity report
generate_capacity_report() {
    cat > "$REPORT_FILE" << EOF
# Monthly Capacity Report - $(date +"%B %Y")

## Executive Summary

Generated on: $(date)
Cluster: $(kubectl config current-context)

## Node Resources

### Current Node Status
\`\`\`
$(kubectl get nodes -o wide)
\`\`\`

### Resource Utilization
\`\`\`
$(kubectl top nodes)
\`\`\`

## Storage Analysis

### Persistent Volume Claims
\`\`\`
$(kubectl get pvc --all-namespaces -o wide)
\`\`\`

### Storage Utilization Trends
EOF

    # Add Longhorn storage details if available
    if kubectl get volumes -n longhorn-system > /dev/null 2>&1; then
        cat >> "$REPORT_FILE" << EOF

### Longhorn Volume Status
\`\`\`
$(kubectl get volumes -n longhorn-system)
\`\`\`

### Storage Health
$(kubectl get volumes -n longhorn-system -o json | jq -r '.items[] | "Volume: \(.metadata.name), Size: \(.spec.size), State: \(.status.state), Robustness: \(.status.robustness)"')
EOF
    fi

    cat >> "$REPORT_FILE" << EOF

## Network Analysis

### Service Distribution
\`\`\`
$(kubectl get svc --all-namespaces | awk '{print $1}' | sort | uniq -c | sort -nr)
\`\`\`

### Ingress Resources
\`\`\`
$(kubectl get ingress --all-namespaces -o wide)
\`\`\`

## Resource Recommendations

EOF

    # Generate resource recommendations
    local total_cpu_requests=0
    local total_memory_requests=0
    local pod_count=0
    
    kubectl get pods --all-namespaces -o json | \
        jq -r '.items[] | "\(.metadata.namespace) \(.metadata.name) \(.spec.containers[0].resources.requests.cpu // "0") \(.spec.containers[0].resources.requests.memory // "0")"' | \
        while read namespace pod cpu memory; do
            ((pod_count++))
            
            # Convert CPU to millicores
            if [[ "$cpu" != "0" ]]; then
                cpu_mc=$(echo "$cpu" | sed 's/m$//' | sed 's/[^0-9]//g')
                total_cpu_requests=$((total_cpu_requests + cpu_mc))
            fi
            
            # Convert memory to MB
            if [[ "$memory" != "0" ]]; then
                memory_mb=$(echo "$memory" | numfmt --from=iec --to-unit=1M)
                total_memory_requests=$((total_memory_requests + memory_mb))
            fi
        done
    
    cat >> "$REPORT_FILE" << EOF

### Current Resource Allocation
- Total Pods: $pod_count
- Total CPU Requests: ${total_cpu_requests}m
- Total Memory Requests: ${total_memory_requests}MB

### Recommendations for Next Month

EOF

    # Check if we're approaching capacity limits
    local node_count=$(kubectl get nodes --no-headers | wc -l)
    local avg_cpu_per_node=$((total_cpu_requests / node_count))
    local avg_memory_per_node=$((total_memory_requests / node_count))
    
    if [[ $avg_cpu_per_node -gt 1500 ]]; then
        echo "- ⚠️  Consider adding more CPU capacity (current average: ${avg_cpu_per_node}m per node)" >> "$REPORT_FILE"
    fi
    
    if [[ $avg_memory_per_node -gt 1500 ]]; then
        echo "- ⚠️  Consider adding more memory capacity (current average: ${avg_memory_per_node}MB per node)" >> "$REPORT_FILE"
    fi
    
    echo "- ✅ Monitor growth trends and plan for 6-month capacity needs" >> "$REPORT_FILE"
    echo "- ✅ Review and optimize resource requests for over-provisioned workloads" >> "$REPORT_FILE"
    
    echo "\nCapacity report generated: $REPORT_FILE"
}

# Main execution
generate_capacity_report
```

## 🔄 Automated Maintenance Scheduling

### Cron Job Configuration

```bash
# Add to root crontab (sudo crontab -e)

# Daily health checks at 6 AM
0 6 * * * /home/johan/scripts/daily-health-check.sh

# Daily cleanup at 2 AM
0 2 * * * /home/johan/scripts/daily-cleanup.sh

# Weekly security updates on Sundays at 3 AM
0 3 * * 0 /home/johan/scripts/weekly-security-updates.sh

# Weekly performance optimization on Saturdays at 4 AM
0 4 * * 6 /home/johan/scripts/weekly-performance-optimization.sh

# Monthly capacity review on the 1st of each month at 7 AM
0 7 1 * * /home/johan/scripts/monthly-capacity-review.sh

# Quarterly full system review (every 3 months on the 1st)
0 8 1 */3 * /home/johan/scripts/quarterly-system-review.sh
```

### Systemd Service for Maintenance

```bash
# Create systemd service for maintenance
sudo tee /etc/systemd/system/homelab-maintenance.service > /dev/null << EOF
[Unit]
Description=Homelab Maintenance Service
After=network.target

[Service]
Type=oneshot
ExecStart=/home/johan/scripts/daily-health-check.sh
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

# Create systemd timer
sudo tee /etc/systemd/system/homelab-maintenance.timer > /dev/null << EOF
[Unit]
Description=Run Homelab Maintenance Daily
Requires=homelab-maintenance.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start timer
sudo systemctl daemon-reload
sudo systemctl enable homelab-maintenance.timer
sudo systemctl start homelab-maintenance.timer
```

## 📊 Maintenance Monitoring

### Grafana Dashboard for Maintenance Metrics

```yaml
# Prometheus rules for maintenance monitoring
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: maintenance-alerts
  namespace: monitoring
spec:
  groups:
  - name: maintenance-health
    rules:
    - alert: MaintenanceScriptFailure
      expr: increase(script_execution_failures_total[24h]) > 0
      for: 0m
      labels:
        severity: warning
      annotations:
        summary: "Maintenance script failed"
        description: "A maintenance script has failed in the last 24 hours"
    
    - alert: HighResourceUtilization
      expr: (
          (node_cpu_seconds_total{mode!="idle"} / node_cpu_seconds_total) > 0.8
        or
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.8
        )
      for: 15m
      labels:
        severity: warning
      annotations:
        summary: "High resource utilization detected"
        description: "Node {{ $labels.instance }} has high resource utilization"
    
    - alert: StorageSpaceLow
      expr: (
          node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes{fstype!="tmpfs"}
        ) < 0.1
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Storage space critically low"
        description: "Filesystem {{ $labels.mountpoint }} has less than 10% free space"
```

## 📅 Maintenance Calendar

### Best Practices Schedule

| Task | Frequency | Best Time | Duration | Impact |
|------|-----------|-----------|----------|--------|
| **Health Checks** | Daily | 6 AM | 5 min | None |
| **Log Cleanup** | Daily | 2 AM | 10 min | None |
| **Security Updates** | Weekly | Sunday 3 AM | 30 min | Low |
| **Performance Review** | Weekly | Saturday 4 AM | 15 min | None |
| **Capacity Planning** | Monthly | 1st, 7 AM | 45 min | None |
| **Full System Review** | Quarterly | 1st, 8 AM | 2 hours | Medium |
| **Hardware Maintenance** | Annually | Planned downtime | 4 hours | High |

### Maintenance Windows

```bash
# Define maintenance windows
cat > /etc/maintenance-windows.conf << EOF
# Homelab Maintenance Windows Configuration

# Daily maintenance (low impact)
DAILY_WINDOW="02:00-06:00"

# Weekly maintenance (moderate impact)
WEEKLY_WINDOW="Saturday 03:00-05:00"

# Monthly maintenance (can include brief service interruptions)
MONTHLY_WINDOW="First Sunday 01:00-03:00"

# Quarterly maintenance (planned downtime allowed)
QUARTERLY_WINDOW="First Saturday of quarter 08:00-12:00"

# Emergency maintenance (as needed)
EMERGENCY_CONTACT="slack-webhook-url"
EOF
```

This comprehensive maintenance strategy ensures your Kubernetes homelab remains healthy, secure, and performant through proactive monitoring and automated maintenance procedures.
