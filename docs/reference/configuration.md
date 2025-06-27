# Configuration Reference

This document provides a comprehensive reference for configuration settings, commands, and templates used throughout the homelab infrastructure.

## Essential Commands

### Kubernetes Commands

```bash
# Get cluster information
kubectl cluster-info

# Get all pods across all namespaces
kubectl get pods --all-namespaces

# Get detailed information about a pod
kubectl describe pod <pod-name> -n <namespace>

# Get logs from a pod
kubectl logs <pod-name> -n <namespace>

# Execute commands in a pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash

# Apply configuration from file
kubectl apply -f <file.yaml>

# Delete resources
kubectl delete -f <file.yaml>
```

### FluxCD Commands

```bash
# Check Flux installation status
flux check

# Get all Flux resources
flux get all

# Get kustomizations
flux get kustomizations

# Get sources
flux get sources git

# Force reconciliation
flux reconcile source git <source-name>
flux reconcile kustomization <kustomization-name>

# Suspend/resume resources
flux suspend kustomization <name>
flux resume kustomization <name>
```

### Longhorn Commands

```bash
# Get Longhorn volumes
kubectl get volumes -n longhorn-system

# Get Longhorn nodes
kubectl get nodes.longhorn.io -n longhorn-system

# Get Longhorn snapshots
kubectl get snapshots -n longhorn-system
```

## Network Configuration

### Cluster Network Settings

```yaml
# K3s network configuration
cluster-cidr: "10.42.0.0/16"
service-cidr: "10.43.0.0/16"
cluster-dns: "10.43.0.10"
```

### MetalLB Configuration

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.1.200-192.168.1.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default
  namespace: metallb-system
spec:
  ipAddressPools:
  - default-pool
```

## Deployment Templates

### Basic Deployment Template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-name
  namespace: default
  labels:
    app: app-name
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app-name
  template:
    metadata:
      labels:
        app: app-name
    spec:
      containers:
      - name: app-name
        image: nginx:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: app-name-service
  namespace: default
spec:
  selector:
    app: app-name
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

### Ingress Template

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-name-ingress
  namespace: default
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    traefik.ingress.kubernetes.io/router.middlewares: "default-secure-headers@kubernetescrd"
spec:
  tls:
  - hosts:
    - app.example.com
    secretName: app-name-tls
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-name-service
            port:
              number: 80
```

## FluxCD Patterns

### Kustomization Template

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: app-name
  namespace: flux-system
spec:
  interval: 5m
  path: "./clusters/staging/apps/app-name"
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
  validation: client
  healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: app-name
    namespace: default
```

### Git Repository Template

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: app-source
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/username/repo
  ref:
    branch: main
```

## Environment Variables

### Common Environment Variables

```bash
# Kubernetes configuration
export KUBECONFIG=~/.kube/config

# Flux CLI configuration
export FLUX_FORWARD_NAMESPACE=flux-system

# GitHub token for Flux
export GITHUB_TOKEN=<your-token>

# Cluster name
export CLUSTER_NAME=homelab
```

## Resource Limits

### Recommended Resource Limits

```yaml
# Small applications
resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"

# Medium applications
resources:
  requests:
    memory: "128Mi"
    cpu: "250m"
  limits:
    memory: "256Mi"
    cpu: "500m"

# Large applications
resources:
  requests:
    memory: "256Mi"
    cpu: "500m"
  limits:
    memory: "512Mi"
    cpu: "1000m"
```

## Validation Scripts

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

echo "Checking cluster health..."
kubectl get nodes
echo ""

echo "Checking system pods..."
kubectl get pods -n kube-system
echo ""

echo "Checking Flux status..."
flux check
echo ""

echo "Checking Longhorn status..."
kubectl get pods -n longhorn-system
```

### Backup Validation Script

```bash
#!/bin/bash
# validate-backup.sh

echo "Validating backups..."

# Check Git repository status
echo "Git repository status:"
git status
echo ""

# Check Longhorn snapshots
echo "Longhorn snapshots:"
kubectl get snapshots -n longhorn-system
echo ""

# Check Velero backups
echo "Velero backups:"
velero backup get
```

## Maintenance Automation

### Update Script

```bash
#!/bin/bash
# update-cluster.sh

echo "Updating cluster components..."

# Update Flux
flux install --export > flux-system.yaml
kubectl apply -f flux-system.yaml

# Force reconciliation
flux reconcile source git flux-system
flux reconcile kustomization flux-system

echo "Update complete!"
```

## Contact Information

- **Administrator**: Johan Hallberg
- **Repository**: https://github.com/username/k8s-cluster-config
- **Documentation**: https://docs.homelab.local
- **Monitoring**: https://grafana.homelab.local
