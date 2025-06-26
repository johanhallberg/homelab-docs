# 🏘️ Staging Environment Status

## 🟢 **Healthy and Operational**

As of the latest update, the homelab staging environment is fully operational, reflecting the intended architecture and configuration.

### 🏗️ Infrastructure Overview

| Component       | Status    | Version | Details                           |
|-----------------|-----------|---------|-----------------------------------|
| **FluxCD**      | Ready     | v2.4.0  | GitOps configured                 |
| **Traefik**     | Ready     | v3.x    | IP: 192.168.100.192               |
| **MetalLB**     | Ready     | Latest  | IP Pool: 192.168.100.180-199      |
| **Longhorn**    | Ready     | Latest  | Storage on NVMe                   |
| **cert-manager**| Ready     | Latest  | Let's Encrypt (Staging)           |

### 📊 Monitoring

All components of the monitoring stack are fully operational, ensuring visibility and alerting across the infrastructure.

| Component       | Status    | Access                                      |
|-----------------|-----------|---------------------------------------------|
| **Prometheus**  | Ready     | [Access Prometheus](https://prometheus.staging.hallonen.se)     |
| **Grafana**     | Ready     | [Access Grafana](https://grafana.staging.hallonen.se)           |
| **Alertmanager**| Ready     | [Access Alertmanager](https://alertmanager.staging.hallonen.se) |
| **Node Exporter**| Ready    | Internal Metrics Collection                 |

### 🔒 Security & Compliance

Robust security and compliance checks are in place, with the environment adhering to best practices.

| Component   | Status   | Details                        |
|-------------|----------|-------------------------------|
| **Polaris** | Ready    | Policy enforcement active     |
| **Auth**    | Configured| Unified Credentials Setup     |
| **TLS**     | Ready    | HTTPS with Let's Encrypt (Staging)|

### 🌐 Service Accessibility

Access to services is available via defined DNS entries, with local network policy ensuring security.

| Service       | URL                                           | Auth Required | Purpose            |
|---------------|-----------------------------------------------|---------------|--------------------|
| **Traefik Dashboard** | [Traefik](https://traefik.staging.hallonen.se)               | Yes       | Ingress Management  |
| **Longhorn**    | [Longhorn](https://longhorn.staging.hallonen.se)                   | Yes       | Storage Management  |
| **Grafana**     | [Grafana](https://grafana.staging.hallonen.se)                    | Yes       | Metrics/Input Monitoring|
| **Prometheus**  | [Prometheus](https://prometheus.staging.hallonen.se)               | Yes       | Data / Indicators   |
| **Alertmanager**| [Alertmanager](https://alertmanager.staging.hallonen.se)           | Yes       | Alert Management    |
| **Polaris**     | [Polaris](https://polaris.staging.hallonen.se)                     | Yes       | Security Assessment |
| **Demo**       | [Demo Site](https://demo.staging.hallonen.se)                      | No        | Public Testing      |

### 🔧 Local DNS Configuration

Ensure Pi-hole DNS settings capture necessary records for local access:

```yaml
# Individual Records
traefik.staging.hallonen.se: 192.168.100.192
grafana.staging.hallonen.se: 192.168.100.192
prometheus.staging.hallonen.se: 192.168.100.192
alertmanager.staging.hallonen.se: 192.168.100.192
polaris.staging.hallonen.se: 192.168.100.192

# Wildcard (Optional)
*.staging.hallonen.se: 192.168.100.192
```

### 🚨 Alerts & Monitoring

Alerts are routed via Discord with clear escalation procedures in place to manage urgent events.

- **Discord** configured for critical alerts
- **Hardware** alerts for ARM devices are live
- **Security** alerts for policy violations
- **Storage** health is monitored

### 🛡️ Security Emphasis

Priority is on unified, secure access:

- **Unified Auth**: Single credential across services
- **HTTPS Only**: Secure end-point delivered online
- **Security Headers**: Managed via Traefik

### ⚙️ Operational Procedures

Troubleshooting and restart operations are optimized.

```bash
# Service Status
kubectl get pods -n monitoring
kubectl get ingress -A

# Test Connectivity
curl -k -u 'admin:[password]' https://192.168.100.192/ \n  -H "Host: grafana.staging.hallonen.se"

# Restart Monitor
kubectl rollout restart deployment -n monitoring

# Restart Ingress
kubectl rollout restart deployment/traefik -n traefik-system
```

---

*This status report consolidates current performance, security adherence, and operational stability as the homelab staging environment matures and evolves.*
