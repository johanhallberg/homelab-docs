# DNS Configuration for Homelab

This document describes how to set up DNS for your homelab services.

## Domain Structure

All services are organized under the `hallonen.se` domain with environment-specific subdomains:

### Staging Environment
- **Base domain**: `staging.hallonen.se`
- **Traefik Dashboard**: `traefik.staging.hallonen.se`
- **Longhorn Storage**: `longhorn.staging.hallonen.se`
- **Grafana**: `grafana.staging.hallonen.se`
- **Prometheus**: `prometheus.staging.hallonen.se`
- **Alertmanager**: `alertmanager.staging.hallonen.se`
- **Polaris**: `polaris.staging.hallonen.se`

### Production Environment
- **Base domain**: `local.hallonen.se`
- **Traefik Dashboard**: `traefik.local.hallonen.se`
- **Longhorn Storage**: `longhorn.local.hallonen.se`
- **Grafana**: `grafana.local.hallonen.se`
- **Prometheus**: `prometheus.local.hallonen.se`
- **Alertmanager**: `alertmanager.local.hallonen.se`
- **Polaris**: `polaris.local.hallonen.se`

## Cloudflare DNS Configuration

### Required DNS Records

Add these DNS records in your Cloudflare dashboard:

#### Staging Environment
```
Type: A
Name: *.staging
Content: 192.168.100.192
Proxy status: 🟠 DNS only
TTL: Auto
```

#### Production Environment  
```
Type: A
Name: *.local
Content: 192.168.100.XXX (production cluster IP)
Proxy status: 🟠 DNS only
TTL: Auto
```

### Cloudflare API Token

1. Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Click "Create Token"
3. Use "Custom token" template
4. Set permissions:
   - **Zone - DNS - Edit**
   - **Zone - Zone - Read**
5. Set zone resources to include your domain
6. Add the token to `infrastructure/traefik/cloudflare-secret.yaml`

## Local DNS (Optional)

For local development and testing, you can add these entries to your `/etc/hosts` file:

### Staging
```
192.168.100.192 traefik.staging.hallonen.se
192.168.100.192 longhorn.staging.hallonen.se
192.168.100.192 grafana.staging.hallonen.se
192.168.100.192 prometheus.staging.hallonen.se
192.168.100.192 alertmanager.staging.hallonen.se
192.168.100.192 polaris.staging.hallonen.se
```

### Production
```
192.168.100.XXX traefik.local.hallonen.se
192.168.100.XXX longhorn.local.hallonen.se
192.168.100.XXX grafana.local.hallonen.se
192.168.100.XXX prometheus.local.hallonen.se
192.168.100.XXX alertmanager.local.hallonen.se
192.168.100.XXX polaris.local.hallonen.se
```

## TLS Certificates

### Let's Encrypt Configuration

The Traefik configuration includes two certificate resolvers:

1. **letsencrypt-staging**: For testing (staging environment)
   - Uses Let's Encrypt staging server
   - Rate limits are more relaxed
   - Certificates show as untrusted in browsers

2. **letsencrypt-prod**: For production
   - Uses Let's Encrypt production server
   - Strict rate limits (5 certificates per domain per week)
   - Trusted certificates

### DNS Challenge

The setup uses DNS-01 challenge with Cloudflare, which allows:
- Wildcard certificates
- Works behind firewalls/NAT
- No need to expose HTTP endpoints

### Certificate Storage

Certificates are stored in Longhorn persistent volumes at `/data/acme.json` within the Traefik pod.

## Troubleshooting

### DNS Resolution Issues

1. **Check Cloudflare DNS propagation**:
   ```bash
   dig @1.1.1.1 traefik.staging.hallonen.se
   ```

2. **Check local DNS resolution**:
   ```bash
   nslookup traefik.staging.hallonen.se
   ```

3. **Check Traefik service**:
   ```bash
   kubectl get svc -n traefik-system traefik
   ```

### Certificate Issues

1. **Check certificate resolver logs**:
   ```bash
   kubectl logs -n traefik-system deployment/traefik | grep acme
   ```

2. **Check Cloudflare API credentials**:
   ```bash
   kubectl get secret -n traefik-system cloudflare-credentials -o yaml
   ```

3. **Test Cloudflare API access**:
   ```bash
   curl -X GET "https://api.cloudflare.com/client/v4/zones" \
        -H "Authorization: Bearer YOUR_API_TOKEN" \
        -H "Content-Type: application/json"
   ```

### Ingress Issues

1. **Check ingress resources**:
   ```bash
   kubectl get ingress --all-namespaces
   ```

2. **Check Traefik dashboard** at `https://traefik.staging.hallonen.se` (staging) or `https://traefik.local.hallonen.se` (production)

3. **Check service endpoints**:
   ```bash
   kubectl get endpoints -n longhorn-system longhorn-frontend
   ```

## Security

### Basic Authentication

All administrative interfaces are protected with basic authentication:
- **Username**: `admin`
- **Password**: `homelab123` (change this!)

To generate new credentials:
```bash
htpasswd -nbB admin "your-new-password"
```

Update the `basic-auth-credentials` secrets in each namespace.

### Network Security

- All HTTP traffic is redirected to HTTPS
- TLS 1.2+ enforced
- Security headers applied
- Rate limiting configured

## Access URLs

Once deployed and DNS is configured:

### Staging Environment
- 🔧 [Traefik Dashboard](https://traefik.staging.hallonen.se)
- 💾 [Longhorn Storage](https://longhorn.staging.hallonen.se)
- 📊 [Grafana](https://grafana.staging.hallonen.se)
- 📈 [Prometheus](https://prometheus.staging.hallonen.se)
- 🚨 [Alertmanager](https://alertmanager.staging.hallonen.se)
- 🔒 [Polaris Security](https://polaris.staging.hallonen.se)

All services require basic authentication (admin/homelab123).
