#!/bin/bash
# Deployment script for ZK Audit System Infrastructure

set -e

echo "🚀 Deploying ZK Audit System Infrastructure"
echo "==========================================="

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk >/dev/null 2>&1; then
    echo "❌ AWS CDK not installed. Please install it with:"
    echo "   npm install -g aws-cdk"
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Get AWS account and region
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "📍 AWS Account: ${ACCOUNT_ID}"
echo "📍 Region: ${REGION}"
echo "📍 CDK Version: $(cdk --version)"

# Set environment variables
export CDK_DEFAULT_ACCOUNT=${ACCOUNT_ID}
export CDK_DEFAULT_REGION=${REGION}

# Step 1: Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

# Step 2: Build Lambda functions
echo ""
echo "🔨 Building Lambda functions..."
cd ../lambda-functions
./build.sh

# Step 3: Create ECR repositories if they don't exist
echo ""
echo "📋 Creating ECR repositories..."
cd ../infrastructure

create_ecr_repo() {
    local repo_name=$1
    echo "Creating ECR repository: ${repo_name}"
    
    if aws ecr describe-repositories --repository-names ${repo_name} --region ${REGION} >/dev/null 2>&1; then
        echo "  ✅ Repository ${repo_name} already exists"
    else
        aws ecr create-repository --repository-name ${repo_name} --region ${REGION} >/dev/null
        echo "  ✅ Created repository ${repo_name}"
    fi
}

create_ecr_repo "zk-audit-block-fetcher"
create_ecr_repo "zk-audit-hash-generator"
create_ecr_repo "zk-audit-stark-prover"
create_ecr_repo "zk-audit-stark-verifier"

# Step 4: Login to ECR
echo ""
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Step 5: Push Docker images to ECR
echo ""
echo "📤 Pushing Docker images to ECR..."
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

push_image() {
    local function_name=$1
    local image_name="zk-audit-${function_name}"
    
    echo "Pushing ${image_name}..."
    docker push ${ECR_REGISTRY}/${image_name}:latest
    echo "  ✅ Pushed ${image_name}"
}

push_image "block-fetcher"
push_image "hash-generator"
push_image "stark-prover"
push_image "stark-verifier"

# Step 6: Bootstrap CDK (if needed)
echo ""
echo "🏗️  Bootstrapping CDK..."
cdk bootstrap aws://${ACCOUNT_ID}/${REGION}

# Step 7: Deploy infrastructure
echo ""
echo "🚀 Deploying infrastructure..."
cdk deploy --require-approval never

echo ""
echo "🎉 Deployment completed successfully!"
echo ""

# Step 8: Get outputs
echo "📋 Stack Outputs:"
echo "=================="
aws cloudformation describe-stacks --stack-name ZkAuditSystemStack --region ${REGION} --query 'Stacks[0].Outputs' --output table

echo ""
echo "✅ ZK Audit System is now deployed and ready to use!"
echo ""
echo "🔗 Next steps:"
echo "  1. Test the system with sample data"
echo "  2. Build and deploy the frontend interface"
echo "  3. Set up monitoring and alerting"