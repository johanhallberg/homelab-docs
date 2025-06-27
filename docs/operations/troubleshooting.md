# 🛠️ Troubleshooting Guide

This guide provides a structured approach to diagnosing and resolving common issues in your Kubernetes homelab.

## 🎯 Troubleshooting Philosophy

Troubleshooting is proactive and systematic, focusing on:
1. **Identification**: Recognizing symptoms and categorizing the problem
2. **Isolation**: Narrowing down the root cause
3. **Resolution**: Applying fixes and validating recovery
4. **Documentation**: Maintaining a log for future reference and learning

## 🔍 Common Issues and Solutions

### 1. Network Problems

**Symptoms**:
- Services inaccessible
- DNS resolution failures

**Diagnosis**:
- Use `ping` to check connectivity between nodes:
  ```bash
  ping <node-IP>
  ```
- Validate network policies using `kubectl`:
  ```bash
  kubectl get networkpolicy -n <namespace>
  ```

**Solutions**:
- Adjust CNI network policies:
  ```bash
  kubectl edit networkpolicy -n <namespace> <policy-name>
  ```
- Correct DNS configurations in `coredns` config map:
  ```bash
  kubectl edit configmap coredns -n kube-system
  ```

### 2. Service Failures

**Symptoms**: 
- Pods not running or crashing
- Service endpoints not responding

**Diagnosis**:
- Check pod logs:
  ```bash
  kubectl logs <pod-name> -n <namespace>
  ```
- Check resource consumption of pods:
  ```bash
  kubectl top pod <pod-name> -n <namespace>
  ```

**Solutions**:
- Restart failed components:
  ```bash
  kubectl rollout restart deployment <deployment-name> -n <namespace>
  ```
- Scale to mitigate load:
  ```bash
  kubectl scale deployment <deployment-name> --replicas=<new-count> -n <namespace>
  ```

### 3. Resource Limits

**Symptoms**:
- Pods evicted due to resource limits
- Performance degradation

**Diagnosis**:
- Describe pod status to identify resource constraints:
  ```bash
  kubectl describe pod <pod-name> -n <namespace>
  ```

**Solutions**:
- Adjust resource quotes and limits:
  ```yaml
  resources:
    requests:
      memory: "128Mi"
      cpu: "250m"
    limits:
      memory: "256Mi"
      cpu: "500m"
  ```
- Use horizontal pod autoscaling to dynamically adjust resources:
  ```bash
  kubectl autoscale deployment <deployment-name> --min=2 --max=10 --cpu-percent=80 -n <namespace>
  ```

## 🧰 Diagnostic Tools

1. **kubectl**: For resource management and querying cluster state
2. **Prometheus/Grafana**: For monitoring metrics and alerts
3. **K9s**: Terminal-based UI for managing Kubernetes clusters and diagnosing issues
4. **netshoot**: Deployable pod for in-depth network troubleshooting

## 🔗 Useful Commands

- List all nodes and their statuses:
  ```bash
  kubectl get nodes -o wide
  ```
- Retrieve pod descriptions across all namespaces:
  ```bash
  kubectl get pods --all-namespaces -o wide
  ```
- Monitor component logs in real-time:
  ```bash
  kubectl logs -f <pod-name> -n <namespace>
  ```
- Get detailed metrics for a cluster component:
  ```bash
  kubectl top node
  ```
- Execute commands inside running pod:
  ```bash
  kubectl exec -it <pod-name> -n <namespace> -- /bin/bash
  ```

## 📝 Documentation Process

Ensure all incidents are documented with: 
1. **Incident timestamp**
2. **Problem description**
3. **Steps to diagnose**
4. **Resolution actions**
5. **Lessons learned**

This documentation helps in building a knowledge base for faster troubleshooting in the future and continuous improvement of the homelab setup.
