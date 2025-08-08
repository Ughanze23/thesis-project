#!/bin/bash
# EC2 Deployment Script for ZK Audit System

set -e

echo "🚀 Starting EC2 deployment..."

# Configuration
INSTANCE_TYPE="t3.medium"
IMAGE_ID="ami-011e15a70256b7f26"  # Amazon Linux 2
KEY_NAME="zk-audit-key"
SECURITY_GROUP_NAME="zk-audit-sg"

# Create security group
echo "📋 Creating security group..."
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP_NAME \
    --description "Security group for ZK Audit System" \
    --query 'GroupId' --output text)

echo "✅ Security group created: $SECURITY_GROUP_ID"

# Add security group rules
echo "🔒 Configuring security group rules..."
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 3000 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0

echo "✅ Security group configured"

# Launch EC2 instance
echo "🖥️ Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $IMAGE_ID \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --user-data file://ec2-user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ZK-Audit-System}]' \
    --query 'Instances[0].InstanceId' --output text)

echo "✅ Instance launched: $INSTANCE_ID"

# Wait for instance to be running
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "🌐 Instance is running at: $PUBLIC_IP"

# Wait for SSH to be available
echo "🔑 Waiting for SSH to be available..."
until nc -z $PUBLIC_IP 22; do
    echo "Waiting for SSH..."
    sleep 5
done

echo "✅ SSH is ready"
echo ""
echo "🎉 Deployment initiated successfully!"
echo "📍 Instance ID: $INSTANCE_ID"
echo "🌐 Public IP: $PUBLIC_IP"
echo "🔗 Frontend: http://$PUBLIC_IP:3000"
echo "🔗 Backend API: http://$PUBLIC_IP:8000"
echo ""
echo "📋 Next steps:"
echo "1. Wait 2-3 minutes for Docker containers to start"
echo "2. Check status: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'docker ps'"
echo "3. View logs: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'docker logs zk-audit-backend'"