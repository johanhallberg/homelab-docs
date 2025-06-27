# Setup Secrets for Staging Environment

Before deploying the staging infrastructure, you need to configure Cloudflare API tokens for both Traefik and cert-manager.

## Cloudflare API Token Setup

1. **Create a Cloudflare API Token**:
   - Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
   - Click "Create Token"
   - Use the "Custom token" template
   - **Permissions**:
     - Zone:Zone:Read
     - Zone:DNS:Edit
   - **Zone Resources**:
     - Include: Specific zone: hallonen.se
   - **Client IP Address Filtering**: (optional, for added security)

2. **Update the secrets in the repository**:

```bash
# For Traefik
sed -i 's/CHANGEME_CLOUDFLARE_API_TOKEN/YOUR_ACTUAL_TOKEN/g' infrastructure/traefik/cloudflare-secret.yaml

# For cert-manager
sed -i 's/CHANGEME_CLOUDFLARE_API_TOKEN/YOUR_ACTUAL_TOKEN/g' infrastructure/cert-manager/cloudflare-secret.yaml
```

## DNS Setup

Ensure your domains are properly configured in Cloudflare:

1. **Staging DNS records** (`staging.hallonen.se`):
   - `A` record: `staging.hallonen.se` → `192.168.100.192` (Staging Traefik LoadBalancer IP)
   - `CNAME` record: `*.staging.hallonen.se` → `staging.hallonen.se`

2. **Production DNS records** (`local.hallonen.se`):
   - `A` record: `local.hallonen.se` → Production Traefik LoadBalancer IP
   - `CNAME` record: `*.local.hallonen.se` → `local.hallonen.se`

2. **Alternative using Cloudflare Tunnel** (recommended for security):
   - Set up a Cloudflare Tunnel pointing to your Traefik IP
   - This avoids exposing your home IP directly

## Verification

After setting up secrets and DNS:

1. **Deploy the infrastructure**:
```bash
flux reconcile kustomization k8s-cluster-config -n flux-system --with-source
```

2. **Check certificate issuance**:
```bash
kubectl get certificates -A
kubectl get certificaterequests -A
```

3. **Test the demo app**:
   - **Staging**: Visit https://demo.staging.hallonen.se
   - **Production**: Visit https://demo.local.hallonen.se
   - Should show nginx welcome page with valid SSL certificate

## Troubleshooting

- **Certificate issues**: Check cert-manager logs: `kubectl logs -n cert-manager deployment/cert-manager`
- **DNS challenge issues**: Verify Cloudflare token permissions
- **Traefik issues**: Check Traefik logs: `kubectl logs -n traefik-system deployment/traefik`

## Security Notes

- Store API tokens securely (consider using external secret management)
- Use least-privilege permissions for API tokens
- Consider rotating tokens regularly
- For production, use separate tokens for staging and production environments
