# Domain Strategy for Environment Separation

## Overview

This homelab uses a clear domain separation strategy to distinguish between staging and production environments:

- **Staging Environment**: `staging.hallonen.se` and `*.staging.hallonen.se`
- **Production Environment**: `local.hallonen.se` and `*.local.hallonen.se`

## Environment Details

### Staging Environment (`staging.hallonen.se`)
- **Platform**: Raspberry Pi 5 + Ubuntu + kubeadm
- **Purpose**: Development, testing, validation
- **Traefik LoadBalancer**: `192.168.100.192`
- **MetalLB Range**: `192.168.100.180-199`
- **Example Services**:
  - Demo App: `demo.staging.hallonen.se`
  - Traefik Dashboard: `traefik.staging.hallonen.se`
  - Longhorn UI: `longhorn.staging.hallonen.se`

### Production Environment (`local.hallonen.se`)
- **Platform**: 3×RK1 + Talos Linux
- **Purpose**: Production workloads, stable services
- **MetalLB Range**: `192.168.100.160-179`
- **Example Services**:
  - Demo App: `demo.local.hallonen.se`
  - Traefik Dashboard: `traefik.local.hallonen.se`
  - Longhorn UI: `longhorn.local.hallonen.se`

## DNS Configuration

### Cloudflare Setup

1. **Create A Records**:
   ```
   staging.hallonen.se    → 192.168.100.192 (Staging Traefik IP)
   local.hallonen.se      → [Production Traefik IP]
   ```

2. **Create Wildcard CNAME Records**:
   ```
   *.staging.hallonen.se  → staging.hallonen.se
   *.local.hallonen.se    → local.hallonen.se
   ```

### Alternative: Cloudflare Tunnel (Recommended)
For better security, use Cloudflare Tunnel instead of exposing IPs directly:
```bash
# Staging tunnel
cloudflared tunnel create staging-homelab
cloudflared tunnel route dns staging-homelab staging.hallonen.se
cloudflared tunnel route dns staging-homelab *.staging.hallonen.se

# Production tunnel  
cloudflared tunnel create production-homelab
cloudflared tunnel route dns production-homelab local.hallonen.se
cloudflared tunnel route dns production-homelab *.local.hallonen.se
```

## Application Deployment Patterns

### Staging Application Example
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-staging
  namespace: my-app
spec:
  rules:
  - host: my-app.staging.hallonen.se
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 80
  tls:
  - hosts:
    - my-app.staging.hallonen.se
    secretName: my-app-staging-tls
```

### Production Application Example
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-production
  namespace: my-app
spec:
  rules:
  - host: my-app.local.hallonen.se
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 80
  tls:
  - hosts:
    - my-app.local.hallonen.se
    secretName: my-app-production-tls
```

## Certificate Management

### Let's Encrypt ClusterIssuers
Both environments use the same ClusterIssuers but different certificates:

```yaml
# Staging certificates use letsencrypt-staging
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: app-staging-tls
spec:
  issuerRef:
    name: letsencrypt-staging
    kind: ClusterIssuer
  dnsNames:
  - app.staging.hallonen.se

# Production certificates use letsencrypt-production  
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: app-production-tls
spec:
  issuerRef:
    name: letsencrypt-production
    kind: ClusterIssuer
  dnsNames:
  - app.local.hallonen.se
```

## Migration Strategy

### From Pi-hole to In-Cluster DNS
When ready to migrate DNS from Pi-hole to Kubernetes:

1. **Phase 1**: Both systems running in parallel
   - Pi-hole handles `hallonen.se` domain
   - Kubernetes handles subdomains (`staging.hallonen.se`, `local.hallonen.se`)

2. **Phase 2**: Gradual migration
   - Move internal services to Kubernetes DNS (Blocky/CoreDNS)
   - Keep external resolution via Cloudflare

3. **Phase 3**: Complete migration
   - All DNS resolution handled by Kubernetes
   - Pi-hole retired or repurposed

## Benefits of This Strategy

1. **Clear Environment Separation**: No confusion about which environment you're accessing
2. **SSL Certificate Management**: Different certificates for different environments
3. **Independent Testing**: Changes in staging don't affect production DNS
4. **Scalable**: Easy to add more environments (e.g., `dev.hallonen.se`)
5. **Professional**: Mirrors real-world enterprise patterns

## Testing Connectivity

```bash
# Test staging environment
curl -H "Host: demo.staging.hallonen.se" http://192.168.100.192/

# Test production environment (once deployed)
curl -H "Host: demo.local.hallonen.se" http://[PRODUCTION_IP]/

# With proper DNS configured
curl https://demo.staging.hallonen.se/
curl https://demo.local.hallonen.se/
```
