# 📊 Monitoring in Kubernetes

This guide covers the comprehensive monitoring stack deployed in the homelab environments, designed for fault detection, performance insights, and capacity planning.

## 🎯 Monitoring Objectives

The monitoring stack aims to provide:

- **Real-time metrics**: Capture key performance indicators
- **Dashboards**: Visual representations of metrics
- **Alerting**: Notification and escalation of issues
- **Logging**: Detailed application logs and audits

## 🛠️ Components Overview

### Prometheus

**Role**: Metrics storage and querying

- **Data Source**: Collects metrics from Kubernetes and application endpoints
- **Data Model**: Time-series data identified by metric names and key/value pairs
- **Storage**: Local storage with optional remote write
- **Queries**: PromQL for extracting insights

**Prometheus Configuration Example**:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: monitoring-prometheus
  namespace: monitoring
spec:
  replicas: 2
  serviceAccountName: prometheus
  version: v2.35.0
  serviceMonitorSelector:
    matchExpressions:
    - key: k8s-app
      operator: In
      values:
      - kube-state-metrics
      - node-exporter
  resources:
    requests:
      memory: 400Mi
  alerting:
    alertmanagers:
    - namespace: monitoring
      name: alertmanager
      port: alertmanager
```

### Grafana

**Role**: Visualization and analysis

- **Dashboards**: Customized dashboards for various metrics
- **Data Sources**: Multiple sources including Prometheus
- **Alerting**: Built-in alerts or via external Prometheus
- **User Access**: Authentication integrated with Kubernetes

**Grafana Custom Dashboard JSON**:

```json
{
  "title": "Cluster Overview",
  "panels": [
    {
      "type": "graph",
      "title": "CPU Usage",
      "targets": [
        {
          "expr": "sum(rate(container_cpu_usage_seconds_total{namespace='default'}[5m]))",
          "legendFormat": "{{\"namespace\": \"default\", \"pod\": \"{{$labels.pod}}\"}}"
        }
      ]
    },
    {
      "type": "singlestat",
      "title": "Memory Usage",
      "targets": [
        {
          "expr": "sum(container_memory_usage_bytes{namespace='default'})",
          "legendFormat": "memory usage (bytes)"
        }
      ]
    }
  ]
}
```

### Alertmanager

**Role**: Alert routing and processing

- **Alert Sources**: Prometheus alerts
- **Configuration**: Routing based on labels
- **Receivers**: Email, Slack, Discord, Webhooks

**Alertmanager Example Rule**:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: critical-rules
  namespace: monitoring
spec:
  groups:
  - name: CriticalAlerts
    rules:
    - alert: HighMemoryUsage
      expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High Memory Usage Detected"
        description: "Node {{ $labels.instance }} memory available is low."
```

## 🚀 Deployment Guides

### Prometheus Deployment

**Deployment Steps**:

1. **Configuration**: Update Prometheus configuration maps
2. **Environment**: Deploy Prometheus via Helm or YAML
3. **Monitoring Targets**: Define ServiceMonitors and PodMonitors
4. **Validation**: Verify targets and alerts

**Prometheus Operator Example**:

```bash
kubectl apply -f monitoring/prometheus-operator/crds/
kubectl apply -f monitoring/prometheus-operator/prometheus-operator.yaml
kubectl apply -f monitoring/prometheus-operator/prometheus.yaml
```

### Grafana Deployment

**Deployment Steps**:

1. **Configuration**: Manage dashboards through ConfigMaps
2. **Access Control**: Set up authentication and RBAC
3. **Data Sources**: Add Prometheus as a data source
4. **Customization**: Import and fine-tune dashboards

**Grafana ConfigMap for Dashboards**:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: monitoring
data:
  cluster-overview.json: |-
    {
      "title": "Cluster Overview",
      "panels": [
        {
          "title": "CPU Usage",
          "type": "graph",
          "targets": [
            {"expr": "sum(rate(container_cpu_usage_seconds_total[5m]))"}
          ]
        }
      ]
    }
```

### Alertmanager Deployment

**Deployment Steps**:

1. **Configuration**: Define alerting rules and receivers
2. **Integrate**: Connect to Prometheus
3. **Validate**: Test alerts and routing

**Alertmanager Config Example**:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yaml: |
    receivers:
      - name: discord-notifications
        webhooks:
          - url: 'https://discordapp.com/api/webhooks/...'
    route:
      receiver: discord-notifications
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 12h
```

## 🔄 Integration with Kubernetes

### Node Exporter

**Purpose**: Collects node-level metrics like CPU, memory, and disk

**Deployment**:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
spec:
  selector:
    matchLabels:
      k8s-app: node-exporter
  template:
    metadata:
      labels:
        k8s-app: node-exporter
    spec:
      containers:
      - image: quay.io/prometheus/node-exporter:v1.3.1
        name: node-exporter
        ports:
        - containerPort: 9100
      nodeSelector:
        kubernetes.io/os: linux
```

### Kube State Metrics

**Purpose**: Provides cluster metrics for resources (nodes, pods, etc.)

**Deployment**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kube-state-metrics
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      k8s-app: kube-state-metrics
  template:
    metadata:
      labels:
        k8s-app: kube-state-metrics
    spec:
      containers:
      - image: quay.io/coreos/kube-state-metrics:v1.9.8
        name: kube-state-metrics
```

## 📈 Best Practices

### Metrics Strategy

- **Define SLOs**: Service Level Objectives with clear metrics
- **Alert Fatigue**: Avoid too many alerts by carefully tuning thresholds
- **Noise Reduction**: Use watchdog alerts for proactive monitoring

### Security Considerations

- **RBAC**: Role-Based Access Control for monitoring components
- **TLS**: Enable transit encryption for metrics
- **Authentication**: Secure Grafana and Alertmanager access

### Performance Tuning

- **Retention Policies**: Balance between data retention and cost
- **Resource Allocation**: Optimize Prometheus and Grafana resource requests
- **Scaling**: Ensure components like Prometheus can handle increase load

---

This monitoring stack ensures strong observability and insight into both cluster and application performance, empowering rapid detection and response to issues within the Kubernetes ecosystem.
