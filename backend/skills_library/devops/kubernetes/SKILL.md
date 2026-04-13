---
name: kubernetes
description: Kubernetes — deployments, services, ingress, helm charts, resource management
---

# Kubernetes

Container orchestration for production workloads.

## Core Objects

- **Pod**: smallest deployable unit (1+ containers sharing network/storage)
- **Deployment**: declarative updates for pods/replicas
- **Service**: stable network endpoint (ClusterIP, NodePort, LoadBalancer)
- **Ingress**: HTTP/S routing to services
- **ConfigMap/Secret**: configuration and sensitive data
- **StatefulSet**: stateful apps with stable identities (databases)
- **DaemonSet**: one pod per node (log collectors, agents)

## Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  selector:
    matchLabels: { app: api }
  template:
    metadata:
      labels: { app: api }
    spec:
      containers:
        - name: api
          image: myregistry/api:1.2.3
          ports: [{ containerPort: 8080 }]
          resources:
            requests: { cpu: "100m", memory: "128Mi" }
            limits:   { cpu: "500m", memory: "512Mi" }
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
            initialDelaySeconds: 10
          readinessProbe:
            httpGet: { path: /ready, port: 8080 }
          env:
            - name: DB_URL
              valueFrom: { secretKeyRef: { name: db, key: url } }
```

## Service + Ingress

```yaml
apiVersion: v1
kind: Service
metadata: { name: api }
spec:
  selector: { app: api }
  ports: [{ port: 80, targetPort: 8080 }]
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt
spec:
  tls: [{ hosts: [api.example.com], secretName: api-tls }]
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend: { service: { name: api, port: { number: 80 } } }
```

## Helm Essentials

```bash
helm create mychart           # scaffold
helm install api ./mychart -f values.prod.yaml
helm upgrade --install api ./mychart --atomic --timeout 5m
helm rollback api 1
helm template api ./mychart   # render without applying
```

Use `values.yaml` + `{{ .Values.image.tag }}` templating. Keep secrets out of Git — use sealed-secrets or external-secrets.

## Best Practices

- Always set resource requests/limits (prevents noisy-neighbor issues)
- Use HorizontalPodAutoscaler for elastic scaling
- Namespace per environment/team; NetworkPolicies for isolation
- Use `kubectl diff` before `apply`; prefer GitOps (ArgoCD/Flux)
- PodDisruptionBudget for high-availability services
- Non-root containers, read-only root filesystem, drop capabilities

## Debugging

```bash
kubectl get pods -n ns -o wide
kubectl describe pod <name>
kubectl logs <pod> -c <container> --previous
kubectl exec -it <pod> -- sh
kubectl port-forward svc/api 8080:80
kubectl top pods   # needs metrics-server
```
