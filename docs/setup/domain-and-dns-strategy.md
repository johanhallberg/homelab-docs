# 🗺️ Domain Strategy and DNS Configuration

## 📜 Overview

This document provides a comprehensive strategy for domain separation, DNS setup, and migration patterns across the homelab environments. This strategy ensures robustness, security, and clear environment separation while allowing for painless migrations and scalability.

## 🔗 Domain Strategy for Environment Separation

### 🎯 Central Idea
- **Staging**: `staging.hallonen.se` - for testing/development
- **Production**: `local.hallonen.se` - for stable services

### 🔒 Cloudflare Configuration

1. **Create A Records**:
   - `staging.hallonen.se` → `192.168.100.192` (Staging)
   - `local.hallonen.se` → [Production IP]

2. **Create Wildcard CNAME Records**:
   - `*.staging.hallonen.se` → `staging.hallonen.se`
   - `*.local.hallonen.se` → `local.hallonen.se`

3. **Alternatively** use **Cloudflare Tunnel**:
   - Secure external access without exposing home IPs

=== "Cloudflare DNS"
    
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

## 🛠️ Application Deployment Patterns

### Example Configurations

=== "Staging Ingress"

    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: app-staging
      namespace: app
    spec:
      rules:
      - host: app.staging.hallonen.se
        http:
          paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-service
                port:
                  number: 80
      tls:
      - hosts:
        - app.staging.hallonen.se
        secretName: app-staging-tls
    ```

=== "Production Ingress"

    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: app-production
      namespace: app
    spec:
      rules:
      - host: app.local.hallonen.se
        http:
          paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-service
                port:
                  number: 80
      tls:
      - hosts:
        - app.local.hallonen.se
        secretName: app-production-tls
    ```

## 🌐 DNS and Certificates

### ClusterIssuers

```yaml
# Staging certificates
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: staging-certificate
spec:
  issuerRef:
    name: letsencrypt-staging
    kind: ClusterIssuer
  dnsNames:
  - app.staging.hallonen.se

# Production certificates
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: production-certificate
spec:
  issuerRef:
    name: letsencrypt-production
    kind: ClusterIssuer
  dnsNames:
  - app.local.hallonen.se
```

## 🔄 Migration Strategy

### Transition Phases

1. **Earlier Stage**:
   - **DNS Provider**: Pi-hole handles `hallonen.se`
   - **Subdomain Management**: Limited within stages

2. **Intermediate Stage**:
   - **DNS Transition**: Use Blocky/CoreDNS for Kubernetes DNS
   - **Cloudflare**: External DNS to remain stable

3. **Final Migration**:
   - **Full DNS via Kubernetes**
   - **Pi-hole**: Optionally decommissioned or repurposed

## 📈 Connectivity Testing

```bash
# Staging environment
curl -H "Host: demo.staging.hallonen.se" http://192.168.100.192/

# Production environment
curl -H "Host: demo.local.hallonen.se" http://[PRODUCTION_IP]/
```

## 🔍 Benefits of This Strategy

1. **Environment Clarity:**
   - Easy-to-understand HR strategy promoting distinct environments

2. **SSL Management**:
   - Separated certificates for environments

3. **Independent Testing**:
   - Safe staging separate from production influence

4. **Scalability**:
   - Adding further domains/environments easily facilitated

5. **Mirror of Best Practice**:
   - Age-old enterprise standard approach to scaled setups
   
6. **Professional Showcase**:
   - Experience aligning with enterprise methodologies

---

*This documentation serves as a practical guide ensuring the homelab's DNS and domain strategies are aligned with modern best practices, aligning with future potential expansions.*
