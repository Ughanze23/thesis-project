#!/bin/bash
# Build script for ZK Audit System Lambda functions

set -e

echo "🏗️  Building ZK Audit System Lambda Functions"
echo "============================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Get AWS account ID for ECR
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "123456789012")
REGION=${AWS_DEFAULT_REGION:-us-east-1}
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "📍 Using AWS Account: ${ACCOUNT_ID}"
echo "📍 Using Region: ${REGION}"
echo "📍 ECR Registry: ${ECR_REGISTRY}"

# Function to build and tag Lambda function
build_function() {
    local function_name=$1
    local image_name="zk-audit-${function_name}"
    
    echo ""
    echo "🔨 Building ${function_name}..."
    
    # Build the specific stage for this function
    docker build --target ${function_name} -t ${image_name}:latest .
    
    # Tag for ECR
    docker tag ${image_name}:latest ${ECR_REGISTRY}/${image_name}:latest
    
    echo "✅ Built ${function_name} successfully"
}

# Build all Lambda functions
echo ""
echo "🚀 Building Lambda functions..."

build_function "block-fetcher"
build_function "hash-generator" 
build_function "stark-prover"
build_function "stark-verifier"

echo ""
echo "📦 Build Summary:"
echo "=================="
docker images | grep "zk-audit-" | head -4

echo ""
echo "🎉 All Lambda functions built successfully!"
echo ""
echo "📝 Next steps:"
echo "  1. Create ECR repositories:"
echo "     aws ecr create-repository --repository-name zk-audit-block-fetcher"
echo "     aws ecr create-repository --repository-name zk-audit-hash-generator"  
echo "     aws ecr create-repository --repository-name zk-audit-stark-prover"
echo "     aws ecr create-repository --repository-name zk-audit-stark-verifier"
echo ""
echo "  2. Login to ECR:"
echo "     aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}"
echo ""
echo "  3. Push images:"
echo "     docker push ${ECR_REGISTRY}/zk-audit-block-fetcher:latest"
echo "     docker push ${ECR_REGISTRY}/zk-audit-hash-generator:latest"
echo "     docker push ${ECR_REGISTRY}/zk-audit-stark-prover:latest"
echo "     docker push ${ECR_REGISTRY}/zk-audit-stark-verifier:latest"
echo ""
echo "  4. Deploy with infrastructure/deploy.sh"