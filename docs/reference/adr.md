# Architecture Decision Records (ADRs)

This document contains the architecture decision records for the homelab infrastructure.

## ADR-001: Kubernetes Distribution Choice

**Status:** Accepted

**Context:** Need to choose a Kubernetes distribution for the homelab cluster.

**Decision:** Use K3s for lightweight, production-ready Kubernetes.

**Consequences:**
- Simplified installation and maintenance
- Lower resource requirements
- Built-in ingress controller and load balancer
- SQLite as default datastore (can be upgraded to etcd)

## ADR-002: GitOps Tool Selection

**Status:** Accepted

**Context:** Need a GitOps tool for continuous deployment.

**Decision:** Use FluxCD v2 for GitOps operations.

**Consequences:**
- Declarative configuration management
- Automated synchronization with Git repositories
- Built-in security scanning and policy enforcement
- Multi-tenancy support

## ADR-003: Storage Solution

**Status:** Accepted

**Context:** Need persistent storage for stateful applications.

**Decision:** Use Longhorn for distributed block storage.

**Consequences:**
- Cloud-native storage with built-in backup capabilities
- Snapshot and disaster recovery features
- Web-based management interface
- Cross-node replication for high availability

## ADR-004: Monitoring Stack

**Status:** Accepted

**Context:** Need comprehensive monitoring and observability.

**Decision:** Use Prometheus + Grafana + AlertManager stack.

**Consequences:**
- Industry-standard monitoring solution
- Rich visualization capabilities
- Flexible alerting rules
- Large ecosystem of exporters and integrations

## ADR-005: Ingress Solution

**Status:** Accepted

**Context:** Need to expose services externally with SSL termination.

**Decision:** Use Traefik as the ingress controller.

**Consequences:**
- Automatic SSL certificate management with Let's Encrypt
- Built-in load balancing and service discovery
- Web-based dashboard for monitoring
- Kubernetes-native configuration

## ADR-006: Secret Management

**Status:** Accepted

**Context:** Need secure secret management for sensitive data.

**Decision:** Use Sealed Secrets for GitOps-compatible secret management.

**Consequences:**
- Secrets can be stored in Git repositories securely
- Asymmetric encryption with cluster-specific keys
- Automatic decryption by the controller
- Compatible with GitOps workflows
