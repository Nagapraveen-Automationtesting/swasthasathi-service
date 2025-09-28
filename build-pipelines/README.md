# Kubernetes Deployment Files for Swasthasathi Service

This directory contains all the necessary Kubernetes deployment files and Jenkins CI/CD configuration for the Swasthasathi Service.

## 📁 Files Overview

| File | Description |
|------|-------------|
| `configmap.yaml` | Non-sensitive environment variables |
| `secret.yaml` | Template for sensitive environment variables (base64 encoded) |
| `deployment.yaml` | Main application deployment configuration |
| `service.yaml` | Kubernetes service to expose the application |
| `hpa.yaml` | Horizontal Pod Autoscaler for scaling |
| `ingress.yaml` | Ingress configuration for external access |
| `mongo-deployment.yaml` | MongoDB deployment (optional) |
| `Jenkinsfile` | Complete CI/CD pipeline configuration |
| `deploy.sh` | Manual deployment script |
| `JENKINS_SETUP.md` | Complete Jenkins setup guide |

## 🚀 Quick Start

### Option 1: Manual Deployment

1. **Update secrets with your values:**
   ```bash
   # Edit secret.yaml and replace base64 encoded values
   # To encode: echo -n "your-value" | base64
   vim secret.yaml
   ```

2. **Deploy to Kubernetes:**
   ```bash
   # Make script executable (Linux/Mac)
   chmod +x deploy.sh
   
   # Deploy everything
   ./deploy.sh deploy
   ```

### Option 2: Individual File Deployment

```bash
# Apply configurations
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml

# Deploy application
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml

# Optional: Deploy ingress
kubectl apply -f ingress.yaml

# Optional: Deploy MongoDB
kubectl apply -f mongo-deployment.yaml
```

### Option 3: Jenkins CI/CD

1. Follow the setup guide in `JENKINS_SETUP.md`
2. Configure all required credentials in Jenkins
3. Create a new pipeline job pointing to the `Jenkinsfile`
4. Trigger the pipeline

## ⚙️ Configuration Required

### Before Deployment, Update These Values:

#### 1. secret.yaml
- Replace all base64 encoded values with your actual credentials
- Generate strong JWT secret key
- Configure Azure Blob Storage credentials
- Set MongoDB connection string
- Configure OCR service URL

#### 2. configmap.yaml
- Update `CORS_ORIGINS` with your frontend domain
- Adjust log levels if needed
- Modify other non-sensitive settings

#### 3. deployment.yaml
- Update the Docker image repository URL
- Adjust resource limits based on your needs
- Modify replica count if needed

#### 4. ingress.yaml
- Replace `api.yourdomain.com` with your actual domain
- Configure SSL/TLS settings
- Adjust ingress class name if needed

## 🔧 Deployment Scripts Usage

The `deploy.sh` script supports multiple operations:

```bash
# Deploy the application
./deploy.sh deploy

# Check deployment status
./deploy.sh status

# View application logs
./deploy.sh logs

# Rollback to previous version
./deploy.sh rollback

# Clean up all resources
./deploy.sh cleanup
```

## 🏥 Health Checks

The deployment includes comprehensive health checks:

- **Startup Probe:** Allows slow container startup (up to 5 minutes)
- **Readiness Probe:** Ensures pod is ready to receive traffic
- **Liveness Probe:** Restarts pod if application becomes unhealthy

All probes use the `/health` endpoint implemented in your FastAPI application.

## 📊 Monitoring and Scaling

### Horizontal Pod Autoscaler (HPA)
The HPA is configured to:
- Maintain 2-10 replicas
- Scale based on CPU (70%) and Memory (80%) usage
- Scale up quickly, scale down gradually

### Resource Management
Each pod is allocated:
- **Requests:** 500m CPU, 512Mi memory
- **Limits:** 1000m CPU, 1Gi memory

Adjust these values in `deployment.yaml` based on your performance requirements.

## 🔒 Security Features

### Container Security
- Runs as non-root user (UID 1000)
- Read-only root filesystem where possible
- Drops all capabilities
- No privilege escalation

### Network Security
- ClusterIP service by default (internal access only)
- Ingress for controlled external access
- Network policies can be added for additional isolation

### Secret Management
- All sensitive data stored in Kubernetes secrets
- Base64 encoding (not encryption - use external secret managers for production)
- No hardcoded credentials in deployment files

## 🌐 External Access

### Option 1: Ingress (Recommended)
- Configure ingress.yaml with your domain
- Requires ingress controller (nginx, traefik, etc.)
- Supports SSL/TLS termination

### Option 2: LoadBalancer Service
- Uncomment the external service in service.yaml
- Provides direct external IP (cloud provider dependent)
- May incur additional costs

### Option 3: NodePort Service
- Change service type to NodePort
- Access via `<node-ip>:<node-port>`
- Less secure, not recommended for production

## 🗄️ Database Options

### Option 1: External MongoDB (Recommended)
- Update `MONGO_CONNECTION_STRING` in secrets
- More reliable and scalable
- Managed service (Atlas, CosmosDB, etc.)

### Option 2: In-Cluster MongoDB
- Deploy using `mongo-deployment.yaml`
- Includes persistent volume for data
- Suitable for development/testing

## 📝 Customization

### Environment-Specific Deployments
To deploy to different environments:

1. **Create namespace-specific files:**
   ```bash
   cp configmap.yaml configmap-prod.yaml
   # Edit environment-specific values
   ```

2. **Use kustomize for environment management:**
   ```bash
   # Create kustomization.yaml for each environment
   # Manage overlays for different configurations
   ```

3. **Use Helm charts for template management:**
   ```bash
   # Convert YAML files to Helm templates
   # Use values files for environment-specific configurations
   ```

## 🚨 Troubleshooting

### Common Issues

1. **Pod Stuck in Pending:**
   ```bash
   kubectl describe pod <pod-name>
   # Check for resource constraints or node selector issues
   ```

2. **ImagePullBackOff:**
   ```bash
   # Check image name and registry access
   kubectl describe pod <pod-name>
   ```

3. **CrashLoopBackOff:**
   ```bash
   # Check application logs
   kubectl logs <pod-name>
   ```

4. **Service Not Accessible:**
   ```bash
   # Check service endpoints
   kubectl get endpoints
   kubectl describe service swasthasathi-service
   ```

### Debug Commands

```bash
# Get all resources
kubectl get all -l app=swasthasathi-service

# Check pod details
kubectl describe deployment swasthasathi-service

# Check recent events
kubectl get events --sort-by=.metadata.creationTimestamp

# Access pod shell for debugging
kubectl exec -it <pod-name> -- /bin/bash

# Port forward for local testing
kubectl port-forward service/swasthasathi-service 8080:80
```

## 🔄 Updates and Rollbacks

### Rolling Updates
The deployment is configured for rolling updates:
- MaxUnavailable: 1 pod
- MaxSurge: 1 pod
- Ensures zero-downtime deployments

### Manual Rollback
```bash
# View rollout history
kubectl rollout history deployment/swasthasathi-service

# Rollback to previous version
kubectl rollout undo deployment/swasthasathi-service

# Rollback to specific revision
kubectl rollout undo deployment/swasthasathi-service --to-revision=2
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Kubernetes and application logs
3. Consult the Jenkins setup guide for CI/CD issues
4. Review the main project documentation

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [FastAPI Deployment Best Practices](https://fastapi.tiangolo.com/deployment/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
