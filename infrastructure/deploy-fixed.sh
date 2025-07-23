#!/bin/bash
# Fixed deployment script for ZK Audit System Infrastructure

set -e

echo "🚀 Deploying ZK Audit System Infrastructure"
echo "==========================================="

# Check prerequisites with better feedback
echo "🔍 Checking prerequisites..."

# Check if AWS CLI is configured
echo "  ⏳ Checking AWS CLI configuration..."
if ! timeout 10 aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured or timed out. Please run 'aws configure' first."
    exit 1
fi
echo "  ✅ AWS CLI configured"

# Check if CDK is installed
echo "  ⏳ Checking AWS CDK installation..."
if ! command -v cdk >/dev/null 2>&1; then
    echo "❌ AWS CDK not installed. Please install it with:"
    echo "   npm install -g aws-cdk"
    exit 1
fi
echo "  ✅ AWS CDK found: $(cdk --version)"

# Check if Docker is running (with timeout and better feedback)
echo "  ⏳ Checking Docker status..."
if timeout 15 docker info >/dev/null 2>&1; then
    echo "  ✅ Docker is running"
elif timeout 15 docker version >/dev/null 2>&1; then
    echo "  ⚠️  Docker client available but daemon may be starting..."
    echo "  ⏳ Waiting for Docker daemon (30s timeout)..."
    for i in {1..30}; do
        if docker info >/dev/null 2>&1; then
            echo "  ✅ Docker daemon ready"
            break
        fi
        sleep 1
        echo -n "."
    done
    if ! docker info >/dev/null 2>&1; then
        echo ""
        echo "❌ Docker daemon failed to start within 30 seconds"
        echo "💡 Please start Docker Desktop manually and wait for it to fully start"
        exit 1
    fi
else
    echo "❌ Docker is not available. Please install Docker Desktop and start it."
    echo "💡 Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Get AWS account and region
echo "🔍 Getting AWS account information..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "📍 AWS Account: ${ACCOUNT_ID}"
echo "📍 Region: ${REGION}"

# Set environment variables
export CDK_DEFAULT_ACCOUNT=${ACCOUNT_ID}
export CDK_DEFAULT_REGION=${REGION}

# Ask user if they want to proceed with full deployment or simplified deployment
echo ""
echo "🤔 Choose deployment option:"
echo "  1) Full deployment (includes Docker builds and ECR)"
echo "  2) Infrastructure only (skip Lambda containers)"
echo "  3) Local development mode (no cloud resources)"
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        FULL_DEPLOYMENT=true
        SKIP_LAMBDA=false
        ;;
    2)
        FULL_DEPLOYMENT=false
        SKIP_LAMBDA=true
        ;;
    3)
        echo "🚀 Starting local development mode..."
        echo "📋 Local development setup:"
        echo "  1. Run: python3 demo.py"
        echo "  2. Run: cd verification-rs && cargo run --bin demo_zk_verification" 
        echo "  3. Run: cd frontend && npm install && npm start"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Defaulting to infrastructure only."
        FULL_DEPLOYMENT=false
        SKIP_LAMBDA=true
        ;;
esac

# Step 1: Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

if [ "$SKIP_LAMBDA" = false ]; then
    # Step 2: Build Lambda functions
    echo ""
    echo "🔨 Building Lambda functions..."
    cd ../lambda-functions
    ./build.sh
    cd ../infrastructure

    # Step 3: Create ECR repositories if they don't exist
    echo ""
    echo "📋 Creating ECR repositories..."

    create_ecr_repo() {
        local repo_name=$1
        echo "  ⏳ Creating ECR repository: ${repo_name}"
        
        if aws ecr describe-repositories --repository-names ${repo_name} --region ${REGION} >/dev/null 2>&1; then
            echo "    ✅ Repository ${repo_name} already exists"
        else
            aws ecr create-repository --repository-name ${repo_name} --region ${REGION} >/dev/null
            echo "    ✅ Created repository ${repo_name}"
        fi
    }

    create_ecr_repo "zk-audit-block-fetcher"
    create_ecr_repo "zk-audit-hash-generator"
    create_ecr_repo "zk-audit-stark-prover"
    create_ecr_repo "zk-audit-stark-verifier"

    # Step 4: Login to ECR
    echo ""
    echo "🔐 Logging in to ECR..."
    if aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com; then
        echo "  ✅ ECR login successful"
    else
        echo "❌ ECR login failed"
        exit 1
    fi

    # Step 5: Push Docker images to ECR
    echo ""
    echo "📤 Pushing Docker images to ECR..."
    ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

    push_image() {
        local function_name=$1
        local image_name="zk-audit-${function_name}"
        
        echo "  ⏳ Pushing ${image_name}..."
        if docker push ${ECR_REGISTRY}/${image_name}:latest; then
            echo "    ✅ Pushed ${image_name}"
        else
            echo "    ❌ Failed to push ${image_name}"
            return 1
        fi
    }

    push_image "block-fetcher" || exit 1
    push_image "hash-generator" || exit 1
    push_image "stark-prover" || exit 1
    push_image "stark-verifier" || exit 1
else
    echo ""
    echo "⏩ Skipping Lambda container builds (infrastructure only mode)"
fi

# Step 6: Bootstrap CDK (if needed)
echo ""
echo "🏗️  Bootstrapping CDK..."
if cdk bootstrap aws://${ACCOUNT_ID}/${REGION}; then
    echo "  ✅ CDK bootstrap completed"
else
    echo "❌ CDK bootstrap failed"
    exit 1
fi

# Step 7: Deploy infrastructure
echo ""
echo "🚀 Deploying infrastructure..."
echo "⏳ This may take 5-10 minutes..."

if [ "$SKIP_LAMBDA" = true ]; then
    echo "⚠️  Note: Lambda functions will be created but won't work until containers are built"
fi

if cdk deploy --require-approval never; then
    echo "  ✅ Infrastructure deployment successful"
else
    echo "❌ Infrastructure deployment failed"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""

# Step 8: Get outputs
echo "📋 Stack Outputs:"
echo "=================="
if aws cloudformation describe-stacks --stack-name ZkAuditSystemStack --region ${REGION} --query 'Stacks[0].Outputs' --output table 2>/dev/null; then
    echo ""
else
    echo "⚠️  Could not retrieve stack outputs (stack may still be deploying)"
fi

echo ""
if [ "$SKIP_LAMBDA" = false ]; then
    echo "✅ ZK Audit System is now fully deployed and ready to use!"
    echo ""
    echo "🔗 Next steps:"
    echo "  1. Test the API endpoints using the URLs above"
    echo "  2. Build and deploy the frontend interface"
    echo "  3. Set up monitoring and alerting"
    echo "  4. Run: python3 ../demo.py to test the system"
else
    echo "✅ Infrastructure deployed! To complete setup:"
    echo ""
    echo "🔗 Next steps:"
    echo "  1. Run this script again with option 1 to build Lambda containers"
    echo "  2. Or run: cd ../lambda-functions && ./build.sh"
    echo "  3. Then: ./deploy.sh (choose option 1)"
    echo "  4. Finally: cd ../frontend && npm install && npm start"
fi

echo ""
echo "💡 For local testing without AWS:"
echo "   python3 ../demo.py"