#!/bin/bash
# EC2 User Data Script - Automatically sets up Docker and deploys ZK Audit System

# Enable logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "🚀 Starting ZK Audit System setup on EC2..."

# Update system
yum update -y

# Install Docker
yum install -y docker git
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install Python and required packages
yum install -y python3 python3-pip
pip3 install pandas numpy tqdm fastapi uvicorn python-multipart pydantic

# Create application directory
mkdir -p /home/ec2-user/zk-audit
cd /home/ec2-user/zk-audit

# Create requirements.txt
cat > requirements.txt << 'EOF'
pandas>=1.5.0
numpy>=1.21.0
tqdm>=4.64.0
boto3>=1.26.0
fastapi>=0.100.0
uvicorn>=0.23.0
python-multipart>=0.0.6
pydantic>=2.0.0
EOF

# Get instance metadata
INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# Create application files directly
cat > fastapi-server.py << 'FASTAPI_EOF'
#!/usr/bin/env python3
"""
FastAPI Server for ZK Audit System
A more robust backend with proper logging and error handling.
"""

import os
import sys
import subprocess
import tempfile
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ZK Audit System API",
    description="Backend API for Zero-Knowledge Audit System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use a proper database)
uploads: Dict[str, dict] = {}
audits: Dict[str, dict] = {}

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str

class UploadResponse(BaseModel):
    success: bool
    upload_id: str
    upload_data: dict
    error: Optional[str] = None

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="ZK Audit FastAPI Server",
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Handle dataset upload and processing."""
    logger.info(f"📁 Upload request: {file.filename}, size: {file.size} bytes")
    
    try:
        # Validate file
        if not file.filename.lower().endswith('.csv'):
            logger.error(f"❌ Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Generate upload ID
        upload_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated upload_id: {upload_id}")
        
        # Save file temporarily
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        # Create simple upload record
        upload_data = {
            'upload_id': upload_id,
            'user_id': 'web_user',
            'filename': file.filename,
            'file_size_mb': file_size_mb,
            'total_blocks': max(4, int(file_size_mb / 2)),
            'data_blocks': max(3, int(file_size_mb / 2) - 1),
            'root_hash': f"hash_{upload_id[:16]}...",
            'timestamp': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        uploads[upload_id] = upload_data
        logger.info(f"✅ Upload completed: {upload_id}")
        
        return {
            'success': True,
            'upload_id': upload_id,
            'upload_data': upload_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/uploads")
async def get_uploads():
    """Get all uploads."""
    return {"uploads": list(uploads.values())}

if __name__ == "__main__":
    print("🚀 Starting ZK Audit FastAPI Server on EC2")
    uvicorn.run(
        "fastapi-server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
FASTAPI_EOF

# Create simple frontend files
mkdir -p frontend-build

cat > frontend-build/index.html << 'HTML_EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZK Audit System</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        input[type="file"] { margin: 10px 0; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .status { margin: 20px 0; padding: 10px; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>🔒 Zero-Knowledge Audit System</h1>
    
    <div class="container">
        <h2>📁 Upload Dataset</h2>
        <input type="file" id="fileInput" accept=".csv" />
        <button onclick="uploadFile()">Upload CSV</button>
        <div id="uploadStatus"></div>
    </div>

    <div class="container">
        <h2>📊 Recent Uploads</h2>
        <button onclick="loadUploads()">Refresh Uploads</button>
        <div id="uploadsDisplay"></div>
    </div>

    <script>
        const API_URL = `http://${window.location.hostname}:8000/api`;
        
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const statusDiv = document.getElementById('uploadStatus');
            
            if (!fileInput.files[0]) {
                statusDiv.innerHTML = '<div class="status error">Please select a file</div>';
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            statusDiv.innerHTML = '<div class="status">Uploading...</div>';
            
            try {
                const response = await fetch(`${API_URL}/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusDiv.innerHTML = `
                        <div class="status success">
                            ✅ Upload successful!<br>
                            Upload ID: ${result.upload_id}<br>
                            File: ${result.upload_data.filename}<br>
                            Size: ${result.upload_data.file_size_mb.toFixed(2)} MB<br>
                            Blocks: ${result.upload_data.total_blocks}
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = `<div class="status error">❌ Upload failed: ${result.error}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">❌ Upload error: ${error.message}</div>`;
            }
        }
        
        async function loadUploads() {
            const displayDiv = document.getElementById('uploadsDisplay');
            displayDiv.innerHTML = 'Loading...';
            
            try {
                const response = await fetch(`${API_URL}/uploads`);
                const data = await response.json();
                
                if (data.uploads && data.uploads.length > 0) {
                    displayDiv.innerHTML = data.uploads.map(upload => `
                        <div class="status success">
                            📁 ${upload.filename} (${upload.file_size_mb.toFixed(2)} MB)<br>
                            🆔 ${upload.upload_id}<br>
                            🕒 ${new Date(upload.timestamp).toLocaleString()}
                        </div>
                    `).join('');
                } else {
                    displayDiv.innerHTML = '<div class="status">No uploads found</div>';
                }
            } catch (error) {
                displayDiv.innerHTML = `<div class="status error">❌ Error loading uploads: ${error.message}</div>`;
            }
        }
        
        // Test API connection on load
        fetch(`${API_URL}/health`)
            .then(response => response.json())
            .then(data => {
                console.log('API Health:', data);
                document.body.insertAdjacentHTML('afterbegin', `
                    <div class="status success">🟢 Connected to backend: ${data.service}</div>
                `);
            })
            .catch(error => {
                document.body.insertAdjacentHTML('afterbegin', `
                    <div class="status error">🔴 Backend connection failed</div>
                `);
            });
    </script>
</body>
</html>
HTML_EOF

# Create Docker Compose file
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  zk-audit-backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped

  zk-audit-frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      - zk-audit-backend
    restart: unless-stopped
COMPOSE_EOF

# Create simple backend Dockerfile
cat > Dockerfile.backend << 'BACKEND_DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY fastapi-server.py .
RUN mkdir -p upload_blocks merkle_commitments logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start application
CMD ["python", "fastapi-server.py"]
BACKEND_DOCKERFILE

# Create simple frontend Dockerfile
cat > Dockerfile.frontend << 'FRONTEND_DOCKERFILE'
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy static files
COPY frontend-build/ /usr/share/nginx/html/

# Create nginx config
RUN echo 'server {' > /etc/nginx/conf.d/default.conf && \
    echo '    listen 3000;' >> /etc/nginx/conf.d/default.conf && \
    echo '    server_name localhost;' >> /etc/nginx/conf.d/default.conf && \
    echo '    root /usr/share/nginx/html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    index index.html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    location / {' >> /etc/nginx/conf.d/default.conf && \
    echo '        try_files $uri $uri/ /index.html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '    location /health {' >> /etc/nginx/conf.d/default.conf && \
    echo '        return 200 "healthy";' >> /etc/nginx/conf.d/default.conf && \
    echo '        add_header Content-Type text/plain;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '}' >> /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
FRONTEND_DOCKERFILE

# Set correct ownership
chown -R ec2-user:ec2-user /home/ec2-user/zk-audit

# Build and start containers
cd /home/ec2-user/zk-audit
sudo -u ec2-user docker-compose up --build -d

echo "✅ ZK Audit System deployment completed!"
echo "🌐 Frontend available at: http://$INSTANCE_IP:3000"
echo "🔧 Backend API at: http://$INSTANCE_IP:8000"
echo "📋 Logs: docker logs zk-audit_zk-audit-backend_1"
FASTAPI_EOF

# Make scripts executable
chmod +x ec2-deploy.sh
chmod +x ec2-user-data.sh

# Now run the deployment
echo "🚀 Starting EC2 deployment..."
./ec2-deploy.sh