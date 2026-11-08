# Kubernetes Platform (On-Prem)

A self-hosted Kubernetes platform designed and operated across Ubuntu virtual machines on two physical servers. The platform runs containerized applications and shared infrastructure services, with GitOps-based deployments, automated monitoring, persistent storage, and secure external connectivity.

It hosts the Mavencrest e-commerce storefront and admin application alongside an observability stack and an automated incident investigation service.

## Architecture

**Application Traffic**

Internet → Cloudflare Tunnel → Kubernetes Services → Application Pods

Traefik Ingress provides additional hostname-based routing.

**GitOps**

GitHub → Argo CD (App-of-Apps) → Kubernetes Cluster

**Observability**

Kubernetes / Traefik → Prometheus → Grafana / Alertmanager

AWS CloudWatch (CloudFront & S3) → Grafana

The cluster is built with kubeadm and containerd, using Flannel for pod networking and Tailscale for secure remote node connectivity.

## Tech Stack

| Category | Technologies |
|---|---|
| Kubernetes | kubeadm, containerd, Helm, Kustomize |
| Automation & GitOps | Ansible, Argo CD, App-of-Apps |
| Networking | Flannel, Traefik, Cloudflare Tunnel, Tailscale |
| Observability | Prometheus, Grafana, Alertmanager, AWS CloudWatch |
| Storage | NFS CSI, PV/PVC |
| Applications | Next.js, Docker, PostgreSQL, GHCR |
| Authentication | Google OAuth, NextAuth.js, Kubernetes Secrets |

## What I Implemented

- **GitOps & Helm:** Implemented Argo CD using the App-of-Apps pattern, with Helm charts and GitHub serving as the deployment and configuration source of truth.
- **Application Hosting:** Deployed the Mavencrest storefront and admin application with Kubernetes Deployments, Services, and container health probes.
- **Container Registry:** Migrated application images from Azure Container Registry to GitHub Container Registry (GHCR), including authentication for private image pulls.
- **Networking & External Access:** Configured Traefik and Cloudflare Tunnel to securely expose applications over HTTPS without opening inbound ports on the host network.
- **Authentication & Secrets:** Integrated Google OAuth and admin email authorization, with application credentials managed through Kubernetes Secrets.
- **Scaling & Availability:** Configured HPA, PodDisruptionBudgets, resource limits, and topology spread constraints to support workload availability and scaling.
- **Infrastructure Automation:** Automated Ubuntu node management and configuration using Ansible.
- **Persistent Storage:** Implemented NFS CSI-backed storage for Grafana and Alertmanager to preserve data when workloads move between worker nodes.
- **Observability:** Deployed Prometheus, Grafana, and Alertmanager for monitoring and alerting, with AWS CloudWatch integrated for visibility into external AWS infrastructure.

## GitOps & Argo CD

Argo CD manages application deployments and platform services using the App-of-Apps pattern. Configuration changes are committed to GitHub and automatically reconciled with the cluster, maintaining consistency between the desired and deployed state.

The Mavencrest storefront and admin applications share a Helm chart, with images hosted in GHCR and application configuration managed through Kubernetes Secrets.

<img src="docs/images/argo.png" alt="Argo CD GitOps Application Dashboard" width="100%">

*Argo CD dashboard showing the applications and platform services managed through GitOps.*

## Observability & Monitoring

The platform uses `kube-prometheus-stack`, deployed through Argo CD, to monitor cluster health, application workloads, and ingress traffic.

Prometheus collects metrics, Grafana provides dashboards, and Alertmanager handles alert routing. AWS CloudWatch is integrated as an additional Grafana data source for monitoring cloud infrastructure alongside Kubernetes.

### AWS CloudFront & S3 Operations Dashboard

Built a custom Grafana dashboard for my AWS-hosted portfolio website, tracking CloudFront requests, HTTP errors, bandwidth consumption, traffic patterns, and S3 storage metrics.

<img src="docs/images/Grafana-dash" alt="AWS CloudFront and S3 Grafana Operations Dashboard" width="100%">

*Grafana dashboard combining CloudFront traffic analytics, error monitoring, and S3 storage metrics.*

**[View Grafana Dashboard JSON](dashboards/cloudfront-s3.json)**

### Traefik Ingress Monitoring

Configured Prometheus metrics collection and ServiceMonitor discovery for Traefik, providing visibility into request volume, response codes, latency, active connections, and ingress performance.

### AIOps — Automated Alert Investigation

Developed a Python-based service that automatically investigates Kubernetes failures and generates AI-assisted incident reports.

- **Prometheus** detects containers in `CrashLoopBackOff`, triggering an authenticated webhook through **Alertmanager**.
- The investigator collects pod status, Kubernetes events, restart counts, and container logs.
- **OpenAI** analyzes the evidence to identify likely causes and recommend troubleshooting steps.
- Reports are persisted and made available in **Grafana** through the Infinity data source.

The service operates with namespace-scoped, read-only RBAC and cannot modify workloads. Credentials are managed through Kubernetes Secrets, and deployment is managed by Argo CD.

**Validated:** A container failure caused by a missing `DATABASE_URL` automatically triggered an investigation, with the incident report displayed in Grafana.

<img src="docs/images/aiops-ss.png" alt="Grafana AIOps investigation dashboard" width="100%">

*Grafana dashboard showing an automated investigation with supporting evidence, probable causes, and recommended actions.*

## Testing & Troubleshooting

Operational work across the platform has included:

- Pod scheduling, recovery, rolling deployments, and node draining.
- HPA tuning, resource allocation, and workload availability.
- Traefik routing, Cloudflare Tunnel connectivity, and HTTPS configuration.
- Kubernetes API, kubelet, and Metrics Server connectivity.
- PersistentVolume/PVC conflicts and NFS-backed workload relocation.
- Argo CD reconciliation, synchronization, and Helm configuration.
- Prometheus ServiceMonitor discovery and Grafana metric queries.
- Resolving `ImagePullBackOff` caused by mixed ARM64/AMD64 worker architectures.
- Configuring private GHCR image pulls, Google OAuth, and application Secrets.

## Repository Structure

```text
Kubernetes-DockingStation/
├── apps/
│   ├── mavencrest/             # Helm chart for Storefront and Admin
│   │   ├── templates/          # Deployments, Services, Ingress, HPA, PDB
│   │   ├── Chart.yaml
│   │   └── values.yaml
│   └── aiops/
│       ├── src/                # Evidence collection, AI analysis, report API
│       ├── k8s/                # Deployment, Service, storage, RBAC, alerting
│       ├── Dockerfile
│       └── requirements.txt
├── platform/
│   ├── applications/           # Argo CD child Applications
│   ├── argocd/                 # Argo CD configuration
│   ├── cloudflared/            # Cloudflare Tunnel
│   ├── local-path-storage/     # Persistent storage provisioner
│   ├── metrics-server/         # Resource metrics
│   └── app-of-apps.yaml        # GitOps bootstrap
├── dashboards/                 # Grafana dashboard definitions
├── docs/
│   └── images/                 # Architecture diagrams and screenshots
└── README.md
```

VM provisioning and operating system management are maintained separately in my Ansible repository.

## Current Limitations

- **Control Plane:** The cluster uses a single control-plane node, so Kubernetes API availability depends on that node.
- **Storage:** NFS enables persistent workload relocation but relies on the underlying NFS server.
- **Infrastructure:** Workloads operate on shared, resource-constrained physical hardware rather than dedicated server infrastructure.

## Project Goal

Operate a Kubernetes platform with repeatable deployments, automated configuration management, centralized monitoring, persistent storage, and reliable application delivery.

The platform provides a foundation for additional workloads, infrastructure automation, and integration with cloud-managed Kubernetes environments such as Amazon EKS and Azure AKS.
