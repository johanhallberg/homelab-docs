# 🌐 Kubernetes Networking

This comprehensive guide covers the networking strategies within our homelab Kubernetes environment, with a focus on Traefik ingress, network policies, and service mesh capabilities.

## 🎯 Networking Objectives

The networking setup is intended to:

- **Facilitate Secure Communication**: Encryption in transit and at REST
- **Enable Ingress and Egress Policies**: Network policy-driven traffic management
- **Load Balancing and Routing**: Ensure optimal application delivery
- **Kubernetes Native Service Discovery**: Utilize Kubernetes service and endpoint resources

## 🧩 Traefik Ingress Controller

### Core Components

**Role**: Handles incoming HTTP(S) requests, forwards to services

```yaml
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: traefik-ingress
  namespace: kube-system
spec:
  chart: traefik
  repo: 'https://helm.traefik.io/traefik'
  targetNamespace: traefik
```

## 🔀 Load Balancing

### Service Types

1. **ClusterIP**: Internal to cluster
2. **NodePort**: Exposes service on each Node's IP
3. **LoadBalancer**: External load balancer specific to cloud providers

## 🔒 Network Policies

### Example: Isolating Sensitive Components

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      role: db
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: api-server
    ports:
    - protocol: TCP
      port: 5432
```

---

This networking approach in the homelab ensures robust and flexible connectivity, with performance and security credentials aligning with modern microservices needs.
