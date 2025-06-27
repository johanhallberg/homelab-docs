# DNS & Reverse Proxy Migration Guide

## Overview
This guide helps you migrate from Pi-hole + Nginx Proxy Manager to Kubernetes-native solutions:
- **DNS**: Pi-hole → Blocky (with ad-blocking)
- **Reverse Proxy**: NPM → Enhanced Traefik
- **Management**: Web-based interfaces for both

## Migration Strategy

### Phase 1: DNS Migration (Pi-hole → Blocky)

#### 1.1 Export Pi-hole Configuration
Before starting, export your Pi-hole data:

```bash
# On your Pi-hole server
sudo pihole -a -t
# This creates a backup in /tmp/

# Export custom DNS records
sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT domain,ip FROM domainlist WHERE type=3;" > pihole_custom_dns.txt

# Export whitelist/blacklist
sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT domain FROM domainlist WHERE enabled=1;" > pihole_lists.txt
```

#### 1.2 Update DNS Mappings
Edit the staging DNS configuration to include your Pi-hole mappings:

```bash
# Edit the staging DNS patches
vim clusters/staging/dns/staging-patches.yaml

# Add your existing DNS mappings to the customDNS.mapping section
# Example:
# router.staging.hallonen.se: 192.168.1.1
# nas.staging.hallonen.se: 192.168.1.100
# printer.staging.hallonen.se: 192.168.1.50
```

#### 1.3 Deploy DNS Stack
```bash
# Commit and push the DNS configuration
git add .
git commit -m "feat: add Kubernetes-native DNS with Blocky"
git push

# Apply DNS infrastructure
kubectl apply -f clusters/staging/infrastructure.yaml

# Monitor deployment
kubectl get pods -n dns-system
kubectl logs -n dns-system deployment/blocky
```

#### 1.4 Test DNS Resolution
```bash
# Test DNS resolution from within the cluster
kubectl run dns-test --image=busybox:1.28 --rm -it --restart=Never -- nslookup staging.hallonen.se 192.168.100.53

# Test from your local machine (once router is configured)
nslookup staging.hallonen.se 192.168.100.53
```

#### 1.5 Update Router Configuration
1. Access your router's admin interface
2. Change primary DNS server to: `192.168.100.53` (Blocky LoadBalancer IP)
3. Keep secondary DNS as your current Pi-hole or use `1.1.1.1`
4. Apply changes and restart router if needed

### Phase 2: Reverse Proxy Migration (NPM → Enhanced Traefik)

#### 2.1 Export NPM Configuration
```bash
# On your NPM server, export proxy host configurations
docker exec nginx-proxy-manager cat /data/nginx/proxy_host/* > npm_configs.txt

# List all proxy hosts for manual review
curl -X GET "http://your-npm-server:81/api/nginx/proxy-hosts" \
  -H "Authorization: Bearer YOUR_NPM_TOKEN"
```

#### 2.2 Create Traefik IngressRoutes
For each NPM proxy host, create a corresponding IngressRoute:

```yaml
# Example migration from NPM to Traefik
# NPM: app.domain.com → http://192.168.1.100:3000
# Traefik:
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: my-app
  namespace: default
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`app.staging.hallonen.se`)
      kind: Rule
      services:
        - name: my-app-service
          port: 3000
  tls:
    secretName: my-app-tls
```

#### 2.3 Access Management Interfaces
After deployment, access your management interfaces:

- **Blocky DNS Management**: `https://dns.staging.hallonen.se`
- **Traefik Dashboard**: `https://traefik.staging.hallonen.se`
- **Grafana Monitoring**: `https://grafana.staging.hallonen.se`

### Phase 3: Monitoring & Observability

#### 3.1 OpenLens Integration
The deployed stack is fully compatible with OpenLens:

1. Connect OpenLens to your cluster
2. Navigate to Network → Services to see LoadBalancer IPs
3. View Workloads → Pods for health status
4. Check Custom Resources → IngressRoutes for routing config

#### 3.2 Prometheus Metrics
Both Blocky and Traefik expose Prometheus metrics:

```bash
# View DNS metrics
kubectl port-forward -n dns-system svc/blocky 4000:4000
curl http://localhost:4000/metrics

# View Traefik metrics  
kubectl port-forward -n traefik-system svc/traefik 8080:8080
curl http://localhost:8080/metrics
```

## Production Migration Plan

### Phase 4: Production Preparation

#### 4.1 Create Production Configuration
```bash
# Create production DNS configuration
mkdir -p clusters/production/dns
cp -r clusters/staging/dns/* clusters/production/dns/

# Update production-specific values
vim clusters/production/dns/production-patches.yaml
```

#### 4.2 Multi-Node Production Setup
For your 3-node RK1 cluster:

```yaml
# Production Blocky configuration
replicaCount: 2  # HA setup
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app.kubernetes.io/name
            operator: In
            values:
            - blocky
        topologyKey: kubernetes.io/hostname
```

## Validation & Testing

### DNS Testing Checklist
- [ ] Internal service resolution (*.staging.hallonen.se)
- [ ] External DNS resolution (google.com, github.com)
- [ ] Ad blocking functionality
- [ ] Custom domain mappings
- [ ] Performance (query response time < 50ms)

### Reverse Proxy Testing Checklist
- [ ] HTTP to HTTPS redirect
- [ ] SSL certificate generation
- [ ] Custom headers and middleware
- [ ] Service discovery and routing
- [ ] Dashboard authentication

### Monitoring Checklist
- [ ] Prometheus metrics collection
- [ ] Grafana dashboard visibility
- [ ] OpenLens cluster visibility
- [ ] Log aggregation and retention

## Rollback Plan

### Emergency Rollback to Pi-hole/NPM
If issues arise, quickly rollback:

```bash
# 1. Update router DNS back to Pi-hole IP
# 2. Remove DNS infrastructure
kubectl delete kustomization infrastructure-dns -n flux-system

# 3. Restore NPM proxy hosts
# 4. Update client configurations
```

## Troubleshooting

### Common Issues

#### Blocky Not Resolving External Domains
```bash
# Check upstream DNS configuration
kubectl logs -n dns-system deployment/blocky | grep upstream

# Test upstream connectivity
kubectl exec -n dns-system deployment/blocky -- nslookup google.com 1.1.1.1
```

#### Traefik Not Routing Traffic
```bash
# Check IngressRoute status
kubectl get ingressroute -A

# Verify service endpoints
kubectl get endpoints -A

# Check Traefik logs
kubectl logs -n traefik-system deployment/traefik
```

#### MetalLB IP Not Assigned
```bash
# Check MetalLB configuration
kubectl get ipaddresspool -A
kubectl get l2advertisement -A

# Verify service status
kubectl get svc -n dns-system dns-lb-staging
```

## Next Steps

1. **Deploy**: Apply the configuration to staging
2. **Test**: Validate DNS and reverse proxy functionality
3. **Monitor**: Verify metrics and dashboards
4. **Migrate**: Plan production deployment
5. **Optimize**: Fine-tune performance based on usage patterns

## Security Considerations

- Use strong authentication for management interfaces
- Regularly update blocklists and security rules
- Monitor for DNS tunneling and suspicious queries
- Implement network policies for service isolation
- Backup configurations and SSL certificates regularly
