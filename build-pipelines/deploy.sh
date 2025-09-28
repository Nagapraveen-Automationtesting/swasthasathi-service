#!/bin/bash
set -e

# Swasthasathi Service Kubernetes Deployment Script
# This script is designed to be run by Jenkins CI/CD pipeline

# Configuration
NAMESPACE=${NAMESPACE:-default}
IMAGE_TAG=${BUILD_NUMBER:-latest}
IMAGE_REPOSITORY=${IMAGE_REPOSITORY:-your-registry/swasthasathi-service}
KUBECONFIG_PATH=${KUBECONFIG_PATH:-~/.kube/config}

echo "🚀 Starting Swasthasathi Service Deployment"
echo "📦 Image: $IMAGE_REPOSITORY:$IMAGE_TAG"
echo "🎯 Namespace: $NAMESPACE"
echo "📅 Timestamp: $(date)"

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo "❌ kubectl is not installed or not in PATH"
        exit 1
    fi
    echo "✅ kubectl is available"
}

# Function to verify cluster connectivity
check_cluster() {
    if ! kubectl cluster-info &> /dev/null; then
        echo "❌ Cannot connect to Kubernetes cluster"
        exit 1
    fi
    echo "✅ Kubernetes cluster is accessible"
}

# Function to create namespace if it doesn't exist
create_namespace() {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo "📁 Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
    else
        echo "✅ Namespace $NAMESPACE already exists"
    fi
}

# Function to apply configurations
apply_configs() {
    echo "⚙️  Applying ConfigMap..."
    kubectl apply -f configmap.yaml -n "$NAMESPACE"
    
    echo "🔐 Applying Secrets..."
    kubectl apply -f secret.yaml -n "$NAMESPACE"
    
    # Optional: Deploy MongoDB (uncomment if you want MongoDB in cluster)
    # echo "🗄️  Applying MongoDB..."
    # kubectl apply -f mongo-deployment.yaml -n "$NAMESPACE"
}

# Function to update deployment with new image
update_deployment() {
    echo "🔄 Updating deployment image..."
    sed -i "s|image: swasthasathi-service:latest|image: $IMAGE_REPOSITORY:$IMAGE_TAG|g" deployment.yaml
    
    kubectl apply -f deployment.yaml -n "$NAMESPACE"
    kubectl apply -f service.yaml -n "$NAMESPACE"
    kubectl apply -f hpa.yaml -n "$NAMESPACE"
    
    # Optional: Apply ingress (uncomment if you have ingress controller)
    # kubectl apply -f ingress.yaml -n "$NAMESPACE"
}

# Function to wait for deployment rollout
wait_for_rollout() {
    echo "⏳ Waiting for deployment rollout..."
    kubectl rollout status deployment/swasthasathi-service -n "$NAMESPACE" --timeout=600s
    
    if [ $? -eq 0 ]; then
        echo "✅ Deployment successful!"
    else
        echo "❌ Deployment failed!"
        kubectl describe deployment/swasthasathi-service -n "$NAMESPACE"
        kubectl logs -l app=swasthasathi-service -n "$NAMESPACE" --tail=50
        exit 1
    fi
}

# Function to verify deployment health
verify_deployment() {
    echo "🏥 Verifying deployment health..."
    
    # Get pod status
    kubectl get pods -l app=swasthasathi-service -n "$NAMESPACE"
    
    # Check if pods are ready
    READY_PODS=$(kubectl get pods -l app=swasthasathi-service -n "$NAMESPACE" -o jsonpath='{.items[*].status.containerStatuses[*].ready}' | grep -c true || true)
    TOTAL_PODS=$(kubectl get pods -l app=swasthasathi-service -n "$NAMESPACE" --no-headers | wc -l)
    
    echo "📊 Ready pods: $READY_PODS/$TOTAL_PODS"
    
    if [ "$READY_PODS" -gt 0 ]; then
        echo "✅ At least one pod is ready"
    else
        echo "❌ No pods are ready"
        kubectl describe pods -l app=swasthasathi-service -n "$NAMESPACE"
        exit 1
    fi
}

# Function to display service information
show_service_info() {
    echo "📋 Service Information:"
    kubectl get services -l app=swasthasathi-service -n "$NAMESPACE"
    
    echo "📋 Ingress Information:"
    kubectl get ingress -l app=swasthasathi-service -n "$NAMESPACE" 2>/dev/null || echo "No ingress found"
    
    echo "📋 HPA Information:"
    kubectl get hpa -l app=swasthasathi-service -n "$NAMESPACE"
}

# Function to cleanup on failure
cleanup_on_failure() {
    echo "🧹 Cleaning up failed deployment..."
    kubectl delete deployment swasthasathi-service -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete service swasthasathi-service -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete hpa swasthasathi-service-hpa -n "$NAMESPACE" --ignore-not-found=true
}

# Main execution
main() {
    echo "🔍 Pre-deployment checks..."
    check_kubectl
    check_cluster
    create_namespace
    
    echo "📦 Deploying application..."
    apply_configs
    update_deployment
    
    echo "⏱️  Monitoring deployment..."
    if wait_for_rollout; then
        verify_deployment
        show_service_info
        echo "🎉 Deployment completed successfully!"
    else
        cleanup_on_failure
        exit 1
    fi
}

# Handle script arguments
case "$1" in
    "deploy")
        main
        ;;
    "rollback")
        echo "🔄 Rolling back deployment..."
        kubectl rollout undo deployment/swasthasathi-service -n "$NAMESPACE"
        wait_for_rollout
        ;;
    "status")
        echo "📊 Deployment status:"
        kubectl get all -l app=swasthasathi-service -n "$NAMESPACE"
        ;;
    "logs")
        echo "📄 Recent logs:"
        kubectl logs -l app=swasthasathi-service -n "$NAMESPACE" --tail=100
        ;;
    "cleanup")
        echo "🗑️  Cleaning up deployment..."
        kubectl delete all -l app=swasthasathi-service -n "$NAMESPACE"
        kubectl delete configmap swasthasathi-service-config -n "$NAMESPACE" --ignore-not-found=true
        kubectl delete secret swasthasathi-service-secrets -n "$NAMESPACE" --ignore-not-found=true
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|status|logs|cleanup}"
        echo "  deploy   - Deploy the application"
        echo "  rollback - Rollback to previous version"
        echo "  status   - Show deployment status"
        echo "  logs     - Show application logs"
        echo "  cleanup  - Remove all resources"
        exit 1
        ;;
esac
