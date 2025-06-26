# 🔐 Secrets Setup and Configuration

This guide covers the essential security configuration for the homelab environment, including API tokens, authentication, and SSL certificate management.

## 🌤️ Cloudflare API Token Setup

Before deploying infrastructure, configure Cloudflare API tokens for both Traefik and cert-manager to enable automatic DNS management and SSL certificates.

### Step 1: Create Cloudflare API Token

1. **Navigate to Cloudflare**:
   - Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
   - Click "Create Token"

2. **Configure Token Permissions**:
   - Use the "Custom token" template
   - **Permissions**:
     - `Zone:Zone:Read`
     - `Zone:DNS:Edit`
   - **Zone Resources**:
     - Include: Specific zone: `hallonen.se`
   - **Client IP Address Filtering**: *(optional, for enhanced security)*

3. **Save the Token**:
   - Copy the generated token immediately
   - Store it securely (you won't see it again)

### Step 2: Update Repository Secrets

```bash
# For Traefik (DNS challenges)
sed -i 's/CHANGEME_CLOUDFLARE_API_TOKEN/YOUR_ACTUAL_TOKEN/g' \
  infrastructure/traefik/cloudflare-secret.yaml

# For cert-manager (certificate issuance)
sed -i 's/CHANGEME_CLOUDFLARE_API_TOKEN/YOUR_ACTUAL_TOKEN/g' \
  infrastructure/cert-manager/cloudflare-secret.yaml
```

!!! warning "Security Best Practice"
    Never commit actual API tokens to version control. Consider using external secret management solutions like External Secrets Operator or Sealed Secrets for production environments.

## 🌐 DNS Configuration

### Required DNS Records

Add these DNS records in your Cloudflare dashboard:

=== "Staging Environment"

    ```yaml
    Type: A
    Name: staging
    Content: 192.168.100.192
    Proxy: DNS only (gray cloud)
    TTL: Auto
    
    Type: CNAME
    Name: *.staging
    Content: staging.hallonen.se
    Proxy: DNS only (gray cloud)
    TTL: Auto
    ```

=== "Production Environment"

    ```yaml
    Type: A
    Name: local
    Content: [Production Traefik IP]
    Proxy: DNS only (gray cloud)
    TTL: Auto
    
    Type: CNAME
    Name: *.local
    Content: local.hallonen.se
    Proxy: DNS only (gray cloud)
    TTL: Auto
    ```

### Alternative: Cloudflare Tunnel

For enhanced security, use Cloudflare Tunnel instead of exposing your home IP:

```bash
# Install cloudflared
# macOS
brew install cloudflared

# Ubuntu/Debian
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Create staging tunnel
cloudflared tunnel create staging-homelab
cloudflared tunnel route dns staging-homelab staging.hallonen.se
cloudflared tunnel route dns staging-homelab *.staging.hallonen.se

# Configure tunnel
cat > ~/.cloudflared/config.yml << EOF
tunnel: staging-homelab
credentials-file: ~/.cloudflared/staging-homelab.json

ingress:
  - hostname: "*.staging.hallonen.se"
    service: http://192.168.100.192
  - service: http_status:404
EOF

# Run tunnel
cloudflared tunnel run staging-homelab
```

## 🔒 Authentication Setup

### Basic Authentication Credentials

Configure unified authentication across all administrative services:

```bash
# Generate password hash
htpasswd -nbB admin "YOUR_SECURE_PASSWORD"

# Update the secret in repository
# Replace the generated hash in infrastructure manifests
```

### Default Credentials

!!! danger "Change Default Credentials"
    The default credentials are:
    
    - **Username**: `admin`
    - **Password**: `[Configure during setup]`
    
    **ALWAYS change these before deployment!**

### Services Requiring Authentication

| Service | URL | Authentication Required |
|---------|-----|------------------------|
| Traefik Dashboard | `https://traefik.staging.hallonen.se` | ✅ |
| Longhorn Storage | `https://longhorn.staging.hallonen.se` | ✅ |
| Grafana | `https://grafana.staging.hallonen.se` | ✅ |
| Prometheus | `https://prometheus.staging.hallonen.se` | ✅ |
| Alertmanager | `https://alertmanager.staging.hallonen.se` | ✅ |
| Polaris Security | `https://polaris.staging.hallonen.se` | ✅ |
| Demo Application | `https://demo.staging.hallonen.se` | ❌ |

## 🚀 Deployment and Verification

### Step 1: Deploy Infrastructure

```bash
# Commit and push secret changes
git add .
git commit -m "feat: configure API tokens and secrets"
git push

# Trigger FluxCD reconciliation
flux reconcile kustomization k8s-cluster-config -n flux-system --with-source
```

### Step 2: Verify Certificate Issuance

```bash
# Check certificate status
kubectl get certificates -A
kubectl get certificaterequests -A

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager
```

### Step 3: Test Service Access

=== "Staging Environment"

    ```bash
    # Test demo app (no auth)
    curl -I https://demo.staging.hallonen.se
    
    # Test authenticated services
    curl -I -u 'admin:YOUR_PASSWORD' https://grafana.staging.hallonen.se
    ```

=== "Production Environment"

    ```bash
    # Test production services (when available)
    curl -I https://demo.local.hallonen.se
    curl -I -u 'admin:YOUR_PASSWORD' https://grafana.local.hallonen.se
    ```

## 🔧 Troubleshooting

### Certificate Issues

```bash
# Check certificate resolver logs
kubectl logs -n traefik-system deployment/traefik | grep acme

# Verify Cloudflare API access
kubectl get secret -n traefik-system cloudflare-credentials -o yaml

# Test API connectivity
curl -X GET "https://api.cloudflare.com/client/v4/zones" \
     -H "Authorization: Bearer YOUR_API_TOKEN" \
     -H "Content-Type: application/json"
```

### DNS Resolution Issues

```bash
# Check DNS propagation
dig @1.1.1.1 staging.hallonen.se
nslookup staging.hallonen.se

# Verify Traefik service
kubectl get svc -n traefik-system traefik
```

### Authentication Problems

```bash
# Check basic auth secret
kubectl get secret -n traefik-system basic-auth-credentials -o yaml

# Verify middleware configuration
kubectl get middleware -A
```

## 🛡️ Security Considerations

### API Token Security

- **Scope**: Use least-privilege permissions (Zone:DNS:Edit, Zone:Zone:Read only)
- **Rotation**: Rotate tokens regularly (quarterly recommended)
- **Storage**: Never store tokens in plain text or version control
- **Monitoring**: Monitor API token usage in Cloudflare dashboard

### Authentication Best Practices

- **Strong Passwords**: Use passwords with >16 characters, mixed case, numbers, symbols
- **Regular Updates**: Change authentication credentials regularly
- **Access Logging**: Monitor service access logs for suspicious activity
- **Network Security**: Ensure services are only accessible over HTTPS

### Network Security

- **TLS Everywhere**: All services use TLS 1.2+ with valid certificates
- **Security Headers**: Traefik applies security headers automatically
- **Rate Limiting**: Configured to prevent abuse
- **Network Policies**: Implement namespace isolation

## 📋 Security Checklist

Before going to production, verify:

- [ ] Cloudflare API tokens configured with minimal permissions
- [ ] Default passwords changed on all services
- [ ] DNS records properly configured
- [ ] SSL certificates issued and valid
- [ ] Basic authentication working on all admin services
- [ ] Security headers applied to all routes
- [ ] Rate limiting configured
- [ ] Access logs monitored

---

*Security is an ongoing process. Regularly review and update configurations, rotate credentials, and monitor for security updates.*
