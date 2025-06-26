# 🚀 Getting Started with the Homelab

Welcome to the comprehensive documentation for Johan's homelab infrastructure! This guide will help you understand the architecture, get started with the environment, and make the most of the available resources.

## 🎯 What is This Homelab?

This homelab is a production-grade Kubernetes environment running on ARM-based hardware, designed for:

- **Learning**: Hands-on experience with enterprise technologies
- **Development**: Testing and developing cloud-native applications
- **Automation**: GitOps-driven infrastructure management
- **Monitoring**: Comprehensive observability and alerting

## 🏗️ Quick Architecture Overview

```mermaid
graph TB
    subgraph "Environments"
        Staging[Staging Environment<br/>Raspberry Pi 4B]
        Production[Production Environment<br/>Turing Pi 2 + RK1]
    end
    
    subgraph "Core Services"
        GitOps[FluxCD GitOps]
        Monitoring[Prometheus + Grafana]
        Storage[Longhorn Storage]
        Ingress[Traefik + TLS]
    end
    
    subgraph "Security"
        Scanner[Trivy Security Scanning]
        Policies[Polaris Policy Enforcement]
        Auth[Unified Authentication]
    end
    
    Staging --> GitOps
    Production --> GitOps
    GitOps --> Monitoring
    GitOps --> Storage
    GitOps --> Ingress
    GitOps --> Scanner
    GitOps --> Policies
    GitOps --> Auth
```

## 📋 Prerequisites

Before diving in, ensure you have:

### Knowledge Requirements
- **Basic Kubernetes**: Understanding of pods, services, deployments
- **Command Line**: Comfort with terminal and basic commands
- **Git**: Basic Git workflow knowledge
- **Networking**: Understanding of DNS, HTTP/HTTPS

### Tools You'll Need
- `kubectl` - Kubernetes CLI
- `flux` - FluxCD CLI (optional but recommended)
- `git` - Version control
- Web browser for accessing dashboards

## 🎯 Quick Start Paths

Choose your path based on your goals:

### 1. Explorer 🔍
**Goal**: Browse and understand the infrastructure

**Path**:
1. Read [Architecture Overview](../architecture/cluster-architecture.md)
2. Check [Staging Status](../management/staging-status.md)
3. Explore service dashboards

### 2. Learner 📚
**Goal**: Learn Kubernetes and GitOps practices

**Path**:
1. Study [Cluster Architecture](../architecture/cluster-architecture.md)
2. Follow [Setup Guides](../setup/secrets-configuration.md)
3. Practice with [Operations](../operations/troubleshooting.md)

### 3. Developer 💻
**Goal**: Deploy applications and experiment

**Path**:
1. Understand [GitOps Workflow](../kubernetes/gitops.md)
2. Review [Application Examples](../applications/services.md)
3. Learn [Monitoring](../kubernetes/monitoring.md)

### 4. Administrator 👨‍💼
**Goal**: Manage and maintain the infrastructure

**Path**:
1. Master [Environment Management](../management/staging-status.md)
2. Configure [Security](../kubernetes/security.md)
3. Handle [Operations](../operations/maintenance.md)

## 🌟 Key Features

### 🔄 GitOps Automation
- **Automated deployments** from Git changes
- **Dependency management** with Renovate
- **Multi-environment** promotion workflow

### 📊 Comprehensive Monitoring
- **Prometheus** metrics collection
- **Grafana** visualization dashboards
- **Alertmanager** with Discord integration
- **ARM-specific** hardware monitoring

### 🛡️ Security First
- **Continuous scanning** with Trivy
- **Policy enforcement** with Polaris
- **TLS everywhere** with automatic certificates
- **Unified authentication** across services

### 💾 Reliable Storage
- **Longhorn** distributed storage
- **Automatic snapshots**
- **Cross-node replication**
- **Backup strategies**

## 🔗 Quick Access Links

### Service Dashboards
- [Grafana Monitoring](https://grafana.staging.hallonen.se)
- [Prometheus Metrics](https://prometheus.staging.hallonen.se)
- [Traefik Dashboard](https://traefik.staging.hallonen.se)
- [Longhorn Storage](https://longhorn.staging.hallonen.se)

### Documentation Sections
- [Architecture](../architecture/cluster-architecture.md) - Technical deep dive
- [Setup](../setup/secrets-configuration.md) - Configuration guides
- [Operations](../operations/troubleshooting.md) - Day-to-day management
- [Reference](../reference/configuration.md) - Quick lookups

## 💡 Tips for Success

### 1. Start Small
- Begin with the staging environment
- Understand one component at a time
- Practice with simple operations first

### 2. Use the Documentation
- This documentation is comprehensive and searchable
- Follow links to dive deeper into topics
- Use the troubleshooting guides when stuck

### 3. Hands-On Learning
- Access the actual dashboards and services
- Try running commands from the examples
- Experiment in staging before production

### 4. Community Resources
- Join Kubernetes and homelab communities
- Follow the referenced documentation links
- Share your learning journey

## 🎓 Learning Path Recommendations

### Week 1: Foundation
- [ ] Read architecture overview
- [ ] Access and explore Grafana dashboards
- [ ] Understand the GitOps workflow
- [ ] Practice basic kubectl commands

### Week 2: Infrastructure
- [ ] Deep dive into networking and DNS
- [ ] Explore storage with Longhorn
- [ ] Learn about security scanning and policies
- [ ] Practice troubleshooting scenarios

### Week 3: Operations
- [ ] Master monitoring and alerting
- [ ] Practice deployment workflows
- [ ] Learn backup and recovery procedures
- [ ] Explore automation possibilities

### Week 4: Advanced Topics
- [ ] Plan your own applications
- [ ] Contribute to the documentation
- [ ] Optimize resource usage
- [ ] Design production readiness

## 🤝 Getting Help

### Documentation
- Use the search feature (top right)
- Check related pages at the bottom
- Follow the troubleshooting guides

### Community
- Kubernetes community resources
- Homelab forums and Discord servers
- GitHub discussions and issues

### Hands-On Support
- All services include monitoring and logging
- Grafana dashboards show system health
- Alerting will notify of issues

---

Ready to begin your homelab journey? Pick a path above and start exploring! 🚀
