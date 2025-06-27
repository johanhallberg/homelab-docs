# 📊 Monitoring Stack

This documentation outlines the monitoring solutions integrated into the Kubernetes homelab for tracking system metrics, performance, and uptime.

## 📈 Monitoring Components

### Prometheus
- **Use Case**: Collect metrics from configured targets, evaluate rule expressions.
- **Why Selected**: Robust community support and customization.
- **Maintainer**: [Prometheus Team](https://prometheus.io)
- **Links**: [GitHub](https://github.com/prometheus/prometheus), [Website](https://prometheus.io)

### Grafana
- **Use Case**: Visualization and analysis of metrics with dashboards.
- **Why Selected**: Extensive plugin support and integrations.
- **Maintainer**: [Grafana Labs](https://grafana.com)
- **Links**: [GitHub](https://github.com/grafana/grafana), [Website](https://grafana.com)

### Alertmanager
- **Use Case**: Manage alerts for Prometheus, including silencing and grouping.
- **Why Selected**: Integrated with Prometheus for seamless processing.
- **Maintainer**: [Prometheus Team](https://prometheus.io)
- **Links**: [GitHub](https://github.com/prometheus/alertmanager), [Website](https://prometheus.io)

### Uptime Kuma
- **Use Case**: Monitoring service status and uptime alerts.
- **Why Selected**: Lightweight and flexible.
- **Maintainer**: [Louis Lam](https://github.com/louislam)
- **Links**: [GitHub](https://github.com/louislam/uptime-kuma), [Website](https://uptime.kuma.pet/)

---
