# Jenkins CI/CD Setup for Swasthasathi Service

This guide explains how to set up Jenkins for automated deployment of the Swasthasathi Service to Kubernetes.

## Prerequisites

1. Jenkins server with Docker support
2. Kubernetes cluster access
3. Docker registry (Docker Hub, ECR, ACR, etc.)
4. Required Jenkins plugins (see below)

## Required Jenkins Plugins

Install these plugins in Jenkins:

1. **Docker Pipeline** - For Docker build/push operations
2. **Kubernetes CLI** - For kubectl commands
3. **Pipeline** - For pipeline functionality
4. **Credentials Binding** - For secure credential handling
5. **Slack Notification** (optional) - For build notifications
6. **Blue Ocean** (optional) - For better pipeline visualization

## Jenkins Credentials Configuration

Configure these credentials in Jenkins (`Manage Jenkins` → `Manage Credentials`):

### 1. Docker Registry Credentials
- **ID:** `docker-registry-credentials`
- **Type:** Username with password
- **Username:** Your Docker registry username
- **Password:** Your Docker registry password/token

### 2. Docker Registry URL
- **ID:** `docker-registry-url`
- **Type:** Secret text
- **Secret:** Your Docker registry URL (e.g., `docker.io`, `your-registry.azurecr.io`)

### 3. Kubernetes Config
- **ID:** `kubernetes-config`
- **Type:** Secret file
- **File:** Your kubeconfig file for cluster access

### 4. Application Secrets
Configure these as **Secret text** credentials:

- **ID:** `mongo-connection-string`
  - **Secret:** Your MongoDB connection string
  
- **ID:** `jwt-secret-key`
  - **Secret:** Your JWT secret key (generate a strong random string)
  
- **ID:** `azure-blob-key`
  - **Secret:** Your Azure Blob Storage access key
  
- **ID:** `azure-blob-account-name`
  - **Secret:** Your Azure Storage account name
  
- **ID:** `azure-blob-container`
  - **Secret:** Your blob container name
  
- **ID:** `ocr-base-url`
  - **Secret:** Your OCR service URL

## Pipeline Setup

1. **Create New Pipeline:**
   - Go to Jenkins dashboard
   - Click "New Item"
   - Enter item name: `swasthasathi-service-pipeline`
   - Select "Pipeline" and click OK

2. **Configure Pipeline:**
   - In the pipeline configuration page:
   - Set "Definition" to "Pipeline script from SCM"
   - Set "SCM" to "Git"
   - Enter your repository URL
   - Set "Script Path" to `build-pipelines/Jenkinsfile`
   - Configure branch specifier (e.g., `*/main` or `*/master`)

3. **Environment Variables (Optional):**
   You can override these in the Jenkins job configuration:
   - `K8S_NAMESPACE` - Kubernetes namespace (default: `default`)
   - `SLACK_CHANNEL` - Slack channel for notifications

## First Run Checklist

Before running the pipeline for the first time:

1. ✅ **Verify Docker Registry Access**
   ```bash
   # Test Docker login
   docker login your-registry-url
   ```

2. ✅ **Verify Kubernetes Access**
   ```bash
   # Test kubectl connectivity
   kubectl cluster-info
   kubectl get nodes
   ```

3. ✅ **Update Image Repository**
   In the Jenkinsfile, update the `DOCKER_REGISTRY` variable to match your registry

4. ✅ **Configure Kubernetes Namespace**
   Update `K8S_NAMESPACE` if you want to deploy to a specific namespace

5. ✅ **Review Security Settings**
   Ensure all secrets are properly configured and encrypted

## Pipeline Stages Explained

The Jenkins pipeline includes these stages:

1. **Checkout** - Get source code from Git
2. **Build Docker Image** - Build the application Docker image
3. **Security Scan** - Run Trivy security scan (optional)
4. **Push to Registry** - Push image to Docker registry
5. **Prepare Deployment** - Update Kubernetes manifests with new image tag
6. **Deploy to Kubernetes** - Apply all Kubernetes resources
7. **Verify Deployment** - Check deployment status and health

## Monitoring and Troubleshooting

### Build Logs
- Check Jenkins build logs for detailed information
- Look for error messages in the "Console Output"

### Kubernetes Troubleshooting
```bash
# Check pod status
kubectl get pods -n your-namespace

# Check pod logs
kubectl logs -l app=swasthasathi-service -n your-namespace

# Check deployment status
kubectl describe deployment swasthasathi-service -n your-namespace

# Check service status
kubectl get services -n your-namespace
```

### Common Issues

1. **Docker Build Failures**
   - Check Dockerfile syntax
   - Verify base image availability
   - Check Docker daemon connectivity

2. **Image Push Failures**
   - Verify Docker registry credentials
   - Check network connectivity to registry
   - Verify registry permissions

3. **Kubernetes Deployment Failures**
   - Check kubeconfig validity
   - Verify cluster connectivity
   - Check resource quotas
   - Review secret/configmap values

4. **Pod Startup Issues**
   - Check environment variables
   - Verify database connectivity
   - Review application logs

## Security Best Practices

1. **Never hardcode secrets** in Jenkinsfile or YAML files
2. **Use Jenkins credentials** for all sensitive data
3. **Rotate secrets regularly** (JWT keys, database passwords, etc.)
4. **Limit Jenkins permissions** to necessary Kubernetes namespaces
5. **Use RBAC** in Kubernetes for fine-grained access control
6. **Enable audit logging** in both Jenkins and Kubernetes
7. **Regular security scans** using tools like Trivy

## Advanced Configuration

### Multi-Environment Deployment
To deploy to multiple environments (dev, staging, prod):

1. Create separate branches (dev, staging, main)
2. Configure different Jenkins jobs for each environment
3. Use different Kubernetes namespaces
4. Manage environment-specific secrets separately

### Blue-Green Deployment
For zero-downtime deployments:

1. Use Kubernetes deployment strategies
2. Configure readiness/liveness probes properly
3. Implement health checks
4. Use rolling updates with proper resource limits

### GitOps Integration
For GitOps workflows:

1. Consider using ArgoCD or Flux
2. Store Kubernetes manifests in separate Git repository
3. Use Jenkins only for building and pushing images
4. Let GitOps operator handle deployments

## Support and Maintenance

### Regular Tasks
- Monitor build success rates
- Update base Docker images regularly
- Review and rotate credentials quarterly
- Monitor resource usage in Kubernetes
- Update Jenkins plugins regularly

### Backup Strategy
- Backup Jenkins configuration
- Backup Kubernetes cluster state
- Backup database regularly
- Document recovery procedures
