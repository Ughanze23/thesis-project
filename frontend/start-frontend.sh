#!/bin/bash
# Start the ZK Audit Frontend

echo "🚀 Starting ZK Audit Frontend"
echo "=============================="

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if .env exists, if not copy from example
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📄 Creating .env from .env.example..."
        cp .env.example .env
    else
        echo "📄 Creating default .env..."
        cat > .env << EOF
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_ENVIRONMENT=development
EOF
    fi
fi

echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🔗 Make sure the API server is running at: http://localhost:5000"
echo ""
echo "💡 To start the API server:"
echo "   python3 ../local-api-server.py"
echo ""
echo "Starting development server..."

npm start