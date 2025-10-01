#!/bin/bash

# Deployment script for swasthasathi-service
set -e

echo "🔧 Deploying swasthasathi-service..."

# Check if deployment exists
if kubectl get deployment swasthasathi-service -n swasthasathi >/dev/null 2>&1; then
    echo "📦 Existing deployment found, deleting it first..."
    kubectl delete deployment swasthasathi-service -n swasthasathi --ignore-not-found=true
    echo "⏳ Waiting for pods to terminate..."
    kubectl wait --for=delete pod -l app=swasthasathi-service -n swasthasathi --timeout=60s || true
fi

echo "🚀 Applying new deployment..."

# Apply configurations in order
echo "📋 Applying ConfigMap..."
kubectl apply -f configmap.yaml -n swasthasathi

echo "🔐 Applying Secrets..."
kubectl apply -f secret.yaml -n swasthasathi

echo "🚀 Applying Application Deployment..."
kubectl apply -f deployment.yaml -n swasthasathi
kubectl apply -f service.yaml -n swasthasathi
kubectl apply -f loadbalancer.yaml -n swasthasathi

echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available deployment/swasthasathi-service -n swasthasathi --timeout=300s

echo "✅ Deployment completed successfully!"