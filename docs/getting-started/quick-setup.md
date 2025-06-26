# ⚡ Quick Setup Guide

This guide provides a rapid deployment path for getting the homelab infrastructure up and running.

## 🎯 Prerequisites

- Kubernetes cluster (staging: Raspberry Pi 4B)
- kubectl configured and working
- Git repository access
- Basic understanding of Kubernetes concepts

## 🚀 5-Minute Quick Start

### 1. Verify Cluster Access
```bash
kubectl get nodes
kubectl get namespaces
```

### 2. Check Current Deployments
```bash
kubectl get pods --all-namespaces
kubectl get services --all-namespaces
```

### 3. Access Services
Your homelab should already be running with these services:

- **Grafana**: https://grafana.staging.hallonen.se
- **Prometheus**: https://prometheus.staging.hallonen.se
- **Traefik**: https://traefik.staging.hallonen.se
- **Longhorn**: https://longhorn.staging.hallonen.se

### 4. Verify GitOps
```bash
# Check FluxCD status
flux get kustomizations
flux get sources git
```

## 🔧 Common First Steps

### Deploy a Test Application
```bash
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=ClusterIP
```

### Check Monitoring
```bash
# View cluster metrics in Grafana
# Navigate to: https://grafana.staging.hallonen.se
# Default login: admin / [configured password]
```

### Explore Storage
```bash
# Check Longhorn volumes
kubectl get pv
kubectl get pvc --all-namespaces
```

For detailed setup instructions, see the [comprehensive setup guides](../setup/secrets-configuration.md).
