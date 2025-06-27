# 🚇 Cloudflare Tunnel Setup for Documentation Site

## 🎯 Overview

Your documentation site has been deployed to Kubernetes with Cloudflare Tunnel support! This guide will help you complete the setup for secure, authenticated access to your documentation.

## 📋 Current Status

✅ **Deployed to Kubernetes:**
- Namespace: `docs`
- MkDocs site: Running with comprehensive homelab documentation
- Cloudflare Tunnel: Ready for configuration
- Local access: Available via Traefik ingress

## 🔧 Step 1: Create Cloudflare Tunnel

### 1.1 Install cloudflared (if not already installed)

```bash
# macOS
brew install cloudflared

# Ubuntu/Debian
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Or use the official installer
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

### 1.2 Authenticate with Cloudflare

```bash
# This will open a browser for authentication
cloudflared tunnel login
```

### 1.3 Create the tunnel

```bash
# Create a tunnel named 'docs-homelab'
cloudflared tunnel create docs-homelab

# Note the Tunnel ID that gets generated
# Example output: Created tunnel docs-homelab with id: 12345678-1234-1234-1234-123456789abc
```

### 1.4 Get tunnel credentials

```bash
# The credentials file is created at ~/.cloudflared/[TUNNEL_ID].json
# Copy the content - you'll need it for the Kubernetes secret
cat ~/.cloudflared/[YOUR_TUNNEL_ID].json
```

## 🔐 Step 2: Update Kubernetes Secret

### 2.1 Update the tunnel credentials

Edit the secret with your actual tunnel credentials:

```bash
kubectl edit secret cloudflare-tunnel-credentials -n docs
```

Replace the `credentials.json` content with your actual tunnel credentials from `~/.cloudflared/[TUNNEL_ID].json`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cloudflare-tunnel-credentials
  namespace: docs
type: Opaque
stringData:
  credentials.json: |
    {
      "AccountTag": "your-actual-account-tag",
      "TunnelSecret": "your-actual-tunnel-secret",
      "TunnelID": "your-actual-tunnel-id"
    }
```

### 2.2 Update the tunnel configuration (optional)

```bash
kubectl edit configmap cloudflare-tunnel-config -n docs
```

Update the tunnel name if different:

```yaml
data:
  config.yaml: |
    tunnel: docs-homelab  # Make sure this matches your tunnel name
    credentials-file: /etc/cloudflared/credentials.json
    metrics: 0.0.0.0:2000
    ingress:
      - hostname: docs.staging.hallonen.se
        service: http://mkdocs-site:80
      - service: http_status:404
```

## 🌐 Step 3: Configure DNS

### 3.1 Route DNS to your tunnel

```bash
# Route the documentation subdomain to your tunnel
cloudflared tunnel route dns docs-homelab docs.staging.hallonen.se
```

### 3.2 Verify DNS routing

```bash
# Check that the DNS record was created
dig docs.staging.hallonen.se
```

## 🔒 Step 4: Set Up Cloudflare Access (Authentication)

### 4.1 Navigate to Cloudflare Zero Trust

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Select your account and domain

### 4.2 Create an Access Application

1. Go to **Access** → **Applications**
2. Click **Add an Application**
3. Choose **Self-hosted**
4. Configure the application:

```yaml
Application Configuration:
  Application name: Homelab Documentation
  Session Duration: 24 hours
  Application domain: docs.staging.hallonen.se
  
Access Policies:
  Policy name: Homelab Team Access
  Action: Allow
  Rules: 
    - Email: your-email@domain.com (or your team emails)
    - Country: Your country (optional)
    - IP ranges: Your home IP range (optional)
```

### 4.3 Enable Authentication Methods

Configure your preferred authentication:
- **One-time PIN**: Email-based authentication
- **GitHub**: If you want GitHub OAuth
- **Google**: If you want Google OAuth
- **Custom OIDC**: For other providers

## 🚀 Step 5: Restart and Verify

### 5.1 Restart the Cloudflare Tunnel pods

```bash
kubectl rollout restart deployment/cloudflared-docs -n docs
```

### 5.2 Check pod status

```bash
kubectl get pods -n docs
kubectl logs -f deployment/cloudflared-docs -n docs
```

### 5.3 Test access

1. **External access**: Navigate to `https://docs.staging.hallonen.se`
   - Should prompt for Cloudflare Access authentication
   - After authentication, shows your documentation site

2. **Local access**: Navigate to `https://docs.staging.hallonen.se` (via local DNS)
   - Should work via Traefik ingress without tunnel authentication

## 🔍 Step 6: Verification Checklist

- [ ] Cloudflare tunnel created and configured
- [ ] Kubernetes secret updated with tunnel credentials  
- [ ] DNS record points to tunnel
- [ ] Cloudflare Access application configured
- [ ] External access works with authentication
- [ ] Local access works via Traefik
- [ ] Documentation content loads properly
- [ ] All navigation and links work

## 📊 Step 7: Monitor the Setup

### 7.1 Check tunnel metrics

```bash
# Port forward to access tunnel metrics
kubectl port-forward service/cloudflared-docs-metrics 2000:2000 -n docs

# View metrics at http://localhost:2000/metrics
```

### 7.2 Monitor logs

```bash
# Cloudflare tunnel logs
kubectl logs -f deployment/cloudflared-docs -n docs

# Documentation site logs  
kubectl logs -f deployment/mkdocs-site -n docs

# Content sync logs
kubectl logs -f job/docs-sync-[timestamp] -n docs
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Tunnel not connecting
```bash
# Check tunnel credentials and configuration
kubectl describe secret cloudflare-tunnel-credentials -n docs
kubectl describe configmap cloudflare-tunnel-config -n docs

# Verify tunnel exists in Cloudflare
cloudflared tunnel list
```

#### 2. DNS not resolving
```bash
# Check DNS propagation
dig docs.staging.hallonen.se
nslookup docs.staging.hallonen.se 1.1.1.1

# Verify tunnel route
cloudflared tunnel route dns list
```

#### 3. Authentication not working
- Verify Cloudflare Access application configuration
- Check that the hostname matches exactly
- Ensure authentication policies are correctly configured

#### 4. Documentation not loading
```bash
# Check if MkDocs pods are running
kubectl get pods -n docs
kubectl logs deployment/mkdocs-site -n docs

# Verify content sync
kubectl get jobs -n docs
kubectl logs job/docs-sync-[latest] -n docs
```

## 🎉 Success!

Once complete, you'll have:

✅ **Secure External Access**: Your documentation is accessible externally via Cloudflare Tunnel with authentication  
✅ **Local Access**: Still available locally via Traefik ingress  
✅ **Automatic Updates**: Content syncs automatically from your GitHub repository  
✅ **Professional Documentation**: Beautiful Material theme with all your existing content  
✅ **Zero Exposure**: No ports opened on your home router  

## 🔗 Access URLs

- **External (with auth)**: https://docs.staging.hallonen.se
- **Local (via Traefik)**: https://docs.staging.hallonen.se (with local DNS)
- **Tunnel Metrics**: http://localhost:2000/metrics (via port-forward)

---

*Your documentation site is now enterprise-ready with secure external access and comprehensive homelab documentation!*
