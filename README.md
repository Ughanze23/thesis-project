# ZK Data Integrity Audit System

A cloud-based zero-knowledge data integrity audit system that uses ZK-STARK proofs to verify data hasn't been tampered with, without revealing sensitive information.

## 🎯 Project Overview

This system enables organizations to audit blockchain/financial data with mathematical certainty while preserving complete privacy. It uses:

- **Zero-Knowledge STARK Proofs** for privacy-preserving verification
- **Cryptographically Secure Random Sampling** for 95% confidence corruption detection  
- **Cloud-Native Architecture** with AWS Lambda, S3, and DynamoDB
- **Statistical Guarantees** with provable confidence levels
- **Cost-Effective Auditing** by sampling only a fraction of total data

## 🏗️ Architecture

```
📤 Data Ingestion Pipeline
├── CSV Block Generation (2MB chunks, power of 2)
├── Merkle Tree Construction (SHA3-256)
├── S3 Storage (encrypted, versioned)
└── DynamoDB Metadata (authentication paths)

🔄 Audit Processing Pipeline  
├── Random Block Selection (cryptographically secure)
├── Lambda Functions (containerized Rust)
│   ├── Block Fetcher
│   ├── Hash Generator  
│   ├── STARK Prover
│   └── STARK Verifier
├── Step Functions Orchestration
└── API Gateway (REST API)

🎨 Frontend Interface
├── React + TypeScript
├── Real-time Audit Monitoring
├── Results Visualization
└── Performance Analytics
```

## 🚀 Quick Start

### Prerequisites

- **Rust 1.70+** with nightly toolchain
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **AWS CLI** configured (for cloud deployment, optional)
- **Docker** (for Lambda containerization, optional)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd thesis
```

### 2. Install Dependencies

**Python Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

**Rust Verification System:**
```bash
cd verification-rs
cargo build --release
cd ..
```

### 3. Run the Application

**Option A: Full Web Application (Recommended)**

1. **Start the Backend Server:**
   ```bash
   python3 fastapi-server.py
   ```
   The API will be available at `http://localhost:8000`

2. **Start the Frontend (in a new terminal):**
   ```bash
   cd frontend
   npm start
   ```
   The web interface will open at `http://localhost:3000`

3. **Use the Application:**
   - Upload CSV files through the web interface
   - Configure audit parameters (confidence level, corruption rate)
   - Monitor real-time audit progress
   - View verification results

This includes:
- Sample dataset generation
- Data ingestion and block creation
- Random block selection with 95% confidence
- Zero-knowledge STARK proof generation/verification
- Real-time monitoring and visualization

### 4. Testing the System

**Run Rust tests:**
```bash
cd verification-rs
cargo test
```

**Test the verification system manually:**
- Upload a CSV file through the web interface
- Start an audit with your preferred confidence level
- Monitor the real-time verification progress
- View the detailed results and performance metrics

### 5. Cloud Deployment (Optional)

**Deploy AWS infrastructure:**
```bash
cd infrastructure
./deploy.sh
```

**Build and deploy Lambda functions:**
```bash
cd lambda-functions  
./build.sh
```

## 🔧 Development Setup

### Backend Development

The FastAPI server (`fastapi-server.py`) provides:
- File upload endpoint (`POST /api/upload`)
- Audit management (`POST /api/audit/start`, `GET /api/audit/{id}/status`)
- Real-time status updates
- Integration with Rust verification system

**Key endpoints:**
- `http://localhost:8000/docs` - Interactive API documentation
- `http://localhost:8000/api/health` - Health check
- `http://localhost:8000/api/uploads` - List uploaded files

### Frontend Development

The React frontend provides:
- File upload interface
- Real-time audit monitoring
- Results visualization
- Configuration management

**Development commands:**
```bash
cd frontend
npm start          # Development server
npm run build      # Production build
npm test           # Run tests
```

### Rust Verification System

The verification system (`verification-rs/`) handles:
- Merkle tree verification
- STARK proof generation/verification
- Block integrity checking

**Core functionality:**
- Zero-knowledge STARK proof generation and verification
- Merkle tree validation and integrity checking  
- Integration with the FastAPI backend for seamless web UI operation

## 📂 Project Structure

```
thesis/
├── README.md                          # This file
├── fastapi-server.py                  # Backend API server
├── verification-rs/                   # STARK verification system
│   ├── src/
│   │   ├── lib.rs                     # Core Merkle/STARK functions
│   │   ├── stark.rs                   # STARK proof system
│   │   └── bin/
│   │       └── verify_upload_blocks.rs # Main verification binary
│   └── Cargo.toml
├── cloud_data_ingestion.py           # Cloud-compatible data pipeline
├── random_block_selector.py          # 95% confidence block selection
├── lambda-functions/                  # AWS Lambda functions (Rust)
│   ├── src/
│   │   ├── lib.rs                     # Lambda-compatible library
│   │   ├── stark.rs                   # Cloud STARK implementation
│   │   └── bin/                       # Lambda function handlers
│   ├── Dockerfile                     # Multi-stage Lambda build
│   └── build.sh                       # Build script
├── infrastructure/                    # AWS CDK infrastructure
│   ├── lib/
│   │   └── zk-audit-system-stack.ts  # Complete AWS stack
│   ├── deploy.sh                      # Deployment script
│   └── package.json
├── frontend/                          # React frontend
│   ├── src/
│   │   ├── components/                # Reusable components  
│   │   ├── pages/                     # Main application pages
│   │   └── context/                   # State management
│   └── package.json
├── monitoring/                        # CloudWatch metrics
│   └── cloudwatch-metrics.py         # Metrics collection
└── test_blocks_commitments/           # Sample test data
    ├── merkle_commitment.json
    └── block_*.csv
```

## 🔧 Key Components

### 1. Data Ingestion Pipeline (`cloud_data_ingestion.py`)

- Splits CSV files into 2MB blocks (power of 2 total)
- Builds Merkle trees with SHA3-256 hashing
- Uploads to S3 with proper encryption and versioning
- Stores metadata in DynamoDB for fast queries
- Supports both local and cloud processing modes

### 2. Random Block Selection (`random_block_selector.py`)

- **Statistical Foundation**: Uses binomial probability theory
- **95% Confidence**: Mathematically guaranteed corruption detection
- **Cryptographically Secure**: Uses SHA-256 based deterministic randomness
- **Configurable Parameters**: Adjustable confidence levels and corruption rates
- **Cost Optimization**: Minimizes blocks audited while maintaining guarantees

### 3. STARK Proof System (`verification-rs/`)

- **Zero-Knowledge**: Proves block membership without revealing authentication paths
- **Post-Quantum Security**: Resistant to quantum computer attacks  
- **Constant Proof Size**: ~1KB regardless of Merkle tree height
- **Sub-millisecond Performance**: Fast generation and verification
- **Educational Implementation**: Clear, well-documented code for learning

### 4. Lambda Functions (`lambda-functions/`)

- **Containerized Rust**: High-performance cryptographic operations
- **Scalable Architecture**: Auto-scaling with AWS Lambda
- **Cost-Effective**: Pay only for actual compute time used
- **Monitoring Integration**: CloudWatch metrics and alarms
- **Error Handling**: Comprehensive error recovery and logging

### 5. Frontend Interface (`frontend/`)

- **Real-time Monitoring**: Live audit progress tracking
- **Interactive Configuration**: Confidence level and parameter adjustment
- **Rich Visualizations**: Charts and graphs for results analysis
- **Responsive Design**: Works on desktop and mobile devices
- **TypeScript**: Type-safe development with excellent DX

## 📊 Performance Characteristics

### Proof Sizes
- **Traditional Merkle proof**: 128 bytes (2 sibling hashes × 64 chars)
- **STARK proof**: ~1KB (constant size regardless of tree height)

### Verification Times
- **Traditional verification**: <1ms per block
- **STARK proof generation**: <1ms per block  
- **STARK verification**: <1ms per block

### Scalability
| Tree Height | Total Blocks | Auth Path Size | STARK Proof Size | Compression Ratio |
|-------------|--------------|----------------|------------------|-------------------|
| 10          | 1,024        | 640 bytes      | 1KB              | 1.6x smaller      |
| 16          | 65,536       | 1,024 bytes    | 1KB              | 1.0x same         |
| 20          | 1,048,576    | 1,280 bytes    | 1KB              | 1.3x larger       |
| 24          | 16,777,216   | 1,536 bytes    | 1KB              | 1.5x larger       |

### Cost Analysis
- **Lambda compute**: ~$0.10 per 1,000 audited blocks
- **S3 storage**: ~$0.02 per GB per month
- **DynamoDB operations**: ~$0.01 per 1,000 metadata queries
- **Total estimated cost**: <$1 for typical enterprise audit

## 🛡️ Security Properties

- ✅ **Completeness**: Valid Merkle paths always generate valid proofs
- ✅ **Soundness**: Invalid paths cannot generate valid proofs (2^-128 probability)
- ✅ **Zero-Knowledge**: Proofs reveal no information about authentication paths
- ✅ **Succinctness**: Proof size independent of tree size
- ✅ **Non-Interactive**: No communication required between prover and verifier
- ✅ **Post-Quantum**: Resistant to quantum computer attacks

## 🧪 Testing and Validation

### Automated Testing
```bash
# Run all Rust tests
cd verification-rs && cargo test

# Frontend testing  
cd frontend && npm test

# Backend API testing
# Visit http://localhost:8000/docs for interactive API testing
```

### Manual Testing Scenarios

**1. Normal Operation**
- Upload dataset → Generate blocks → Run audit → Verify results

**2. Tampering Detection**
- Upload a dataset → Manually modify block files in `upload_blocks/` → Run audit → Confirm tampering detected

**3. Performance Testing**
- Large datasets → Measure timing → Validate efficiency

**4. Edge Cases**
- Empty blocks → Small datasets → Network failures

## 🚀 Deployment Options

### Option 1: Web Application (Recommended)
```bash
# Terminal 1: Start backend
python3 fastapi-server.py

# Terminal 2: Start frontend  
cd frontend && npm start

# Open http://localhost:3000 in your browser
```

### Option 2: AWS Cloud Deployment
```bash
cd infrastructure && ./deploy.sh  # Full AWS infrastructure
cd lambda-functions && ./build.sh  # Lambda functions
cd frontend && npm run build  # Frontend build
```

### Option 3: Container Deployment
```bash
# Lambda functions use containerized deployment
docker build -t zk-audit-lambda .
```

## 🐛 Troubleshooting

### Common Issues

**1. Missing Python dependencies:**
```bash
pip install -r requirements.txt
```

**2. Rust compilation errors:**
```bash
cd verification-rs
cargo clean
cargo build --release
```

**3. Frontend build issues:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**4. Port conflicts:**
- Backend runs on port 8000
- Frontend runs on port 3000
- Make sure these ports are available

**5. File upload issues:**
- Ensure the backend server is running before starting frontend
- Check that `fastapi-server.py` shows "Application startup complete"
- Verify API is accessible at `http://localhost:8000/docs`

## 📈 Monitoring and Analytics

### CloudWatch Integration
- **Custom Metrics**: Audit duration, success rates, costs
- **Automated Alarms**: Performance degradation, tampering alerts
- **Custom Dashboards**: Real-time system health monitoring
- **Cost Tracking**: Detailed AWS service usage analysis

### Performance Monitoring
```python
from monitoring.cloudwatch_metrics import ZKAuditMetricsCollector

collector = ZKAuditMetricsCollector()
collector.publish_audit_metrics(metrics)
collector.create_custom_dashboard()
```

## 🤝 Contributing

1. **Development Setup**
   - Install all prerequisites
   - Start the web application to verify setup
   - Make changes in feature branches

2. **Code Standards**
   - Rust: Use `cargo fmt` and `cargo clippy`
   - Python: Follow PEP 8 with black formatting
   - TypeScript: Use ESLint and Prettier
   - Add tests for new functionality

3. **Security Review**
   - All cryptographic code must be reviewed
   - No secrets in code or logs
   - Validate all user inputs

## 📚 Further Reading

- [STARK Paper](https://eprint.iacr.org/2018/046.pdf) - Original STARK research
- [Winterfell Library](https://github.com/facebook/winterfell) - Production STARK implementation
- [Merkle Trees](https://en.wikipedia.org/wiki/Merkle_tree) - Fundamental concepts
- [Zero-Knowledge Proofs](https://en.wikipedia.org/wiki/Zero-knowledge_proof) - Background theory

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Complete README files in each component directory
- **Web Interface**: Interactive frontend for easy testing and validation
- **API Documentation**: Visit `http://localhost:8000/docs` for comprehensive API docs
- **GitHub Issues**: Bug reports and feature requests
- **Community**: Join discussions about ZK proofs and data integrity

---

**Built with ❤️ for secure, privacy-preserving data integrity auditing**