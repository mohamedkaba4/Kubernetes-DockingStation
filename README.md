# Kubernetes Platform (On-Prem)

A self-hosted Kubernetes platform I built and manage across Ubuntu VMs on two physical machines. The goal of this project is to gain hands-on experience with Kubernetes and build a platform using tools and workflows commonly used in production environments like AWS EKS and Azure AKS.

## Architecture

Internet → Cloudflare Tunnel → Traefik Ingress → Kubernetes Services → Application Pods

The cluster uses kubeadm, containerd, Flannel for pod networking, and Tailscale for remote node connectivity.

## Tech Stack

| Category | Technologies |
|---|---|
| Kubernetes | kubeadm, containerd, Helm, Kustomize |
| Automation | Ansible |
| GitOps | Argo CD, App-of-Apps |
| Networking | Flannel, Traefik, Cloudflare Tunnel, Tailscale |
| Monitoring | Prometheus, Grafana, Alertmanager, AWS CloudWatch |
| Storage | NFS CSI, PersistentVolumes, PVCs |
| Application | Next.js, Docker, Azure Container Registry |

## What I Implemented

- **GitOps:** Set up Argo CD with App-of-Apps to manage Kubernetes applications and automatically reconcile changes pushed to GitHub.
- **Application Deployment:** Deployed my Mavencrest e-commerce storefront with health checks, rolling updates, and Kubernetes Services.
- **Ingress:** Configured Traefik and Cloudflare Tunnel to expose the storefront publicly over HTTPS without opening inbound ports on my network.
- **Autoscaling:** Configured HPA to scale application replicas based on CPU usage, along with PodDisruptionBudgets to help maintain availability.
- **Monitoring:** Set up Prometheus, Grafana, and Alertmanager to monitor the cluster and integrated AWS CloudWatch for S3 and CloudFront metrics.
- **Storage:** Configured NFS CSI for persistent storage that can be accessed from different worker nodes, while keeping Prometheus on local storage.

## Testing & Troubleshooting

Tested Pod recovery, scaling, rolling restarts, node draining, and service routing. Also worked through issues involving kubelet certificates, Metrics Server, persistent volumes, scheduling, and connectivity between nodes.

## Limitations

The cluster currently runs with one active control plane, so it doesn't provide full control-plane high availability. The NFS server is also a single point of failure.

## Goal

Build practical Kubernetes and platform engineering experience with a focus on deployment automation, reliability, networking, storage, and observability.
