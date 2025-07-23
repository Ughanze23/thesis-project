# Frontend + Local Demo Integration

## 🎯 Complete Local Experience

This setup connects the React frontend with the local Python/Rust components for a full-stack experience without requiring Docker or AWS.

## 🚀 Quick Start

### 1. Start the Local API Server
```bash
# From the project root
python3 local-api-server.py
```
This starts a Flask server at `http://localhost:5000` that bridges the frontend with your local components.

### 2. Start the Frontend
```bash
# In a new terminal
cd frontend
npm install
npm start
```
The React app will open at `http://localhost:3000`

### 3. Use the Full System
- **Upload CSV files** through the web interface
- **Configure audits** with confidence levels
- **See real results** from your local STARK implementation
- **Monitor performance** with actual timing data

## 🔧 What Happens Behind the Scenes

### File Upload Flow
1. **Frontend**: User uploads CSV file
2. **Local API**: Receives file, saves temporarily
3. **Python Pipeline**: Runs `cloud_data_ingestion.py` 
4. **Results**: Returns block count, Merkle root, processing stats
5. **Frontend**: Shows upload success with real data

### Audit Flow
1. **Frontend**: User selects dataset and configures parameters
2. **Local API**: Runs `random_block_selector.py`
3. **Block Selection**: Uses your statistical algorithms for 95% confidence
4. **STARK Proofs**: If Rust available, runs actual `demo_zk_verification`
5. **Results**: Returns real verification results to frontend

## 📊 Features That Work Locally

### ✅ **Real Functionality**
- Actual CSV file processing
- Real Merkle tree construction  
- Statistical block selection algorithms
- STARK proof generation (if Rust installed)
- Performance timing measurements
- Tampering detection testing

### ✅ **Frontend Features** 
- File drag-and-drop upload
- Real-time processing feedback
- Interactive audit configuration
- Live results visualization
- Performance charts with real data
- Responsive design

## 🔍 API Endpoints

The local server provides:

- `POST /api/upload` - Upload and process CSV files
- `GET /api/uploads` - List processed uploads
- `POST /api/audit/start` - Start audit with your algorithms
- `GET /api/audit/{id}/status` - Get audit results
- `GET /api/health` - Server health check

## 📁 File Structure Integration

```
thesis/
├── local-api-server.py        # ← Flask server bridging frontend/backend
├── cloud_data_ingestion.py    # ← Used by API for file processing
├── random_block_selector.py   # ← Used by API for block selection
├── verification-rs/           # ← Used by API for STARK proofs
└── frontend/
    ├── src/services/api.ts     # ← Connects to local API
    └── .env                    # ← Configure API URL
```

## 🐛 Troubleshooting

### "Connection Refused" Error
- Make sure `python3 local-api-server.py` is running
- Check that port 5000 is not in use
- Verify the API URL in frontend/.env

### Upload Processing Fails  
- Check that CSV file is valid
- Ensure you have Python packages: `pip install flask flask-cors`
- Check terminal output from the API server

### STARK Verification Doesn't Work
- Install Rust: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Build the project: `cd verification-rs && cargo build`
- The system will work without Rust but skip STARK proof generation

### Frontend Won't Start
- Run: `cd frontend && npm install`
- Check Node.js version: `node --version` (needs 16+)
- Clear cache: `npm start -- --reset-cache`

## 🎯 Testing the Complete System

1. **Upload Test**:
   - Create a CSV file with financial data
   - Upload through the web interface
   - Verify it processes into blocks

2. **Audit Test**:
   - Select your uploaded dataset
   - Configure 95% confidence, 5% corruption detection  
   - Start audit and watch real-time progress
   - View detailed results

3. **Performance Test**:
   - Try different file sizes
   - Measure actual processing times
   - Compare with the performance metrics shown

## 🌐 Production Deployment

When you're ready for production:

1. Replace the local API server with AWS infrastructure:
   ```bash
   cd infrastructure && ./deploy-fixed.sh
   ```

2. Update the frontend API URL:
   ```bash
   # In frontend/.env
   REACT_APP_API_URL=https://your-api-gateway-url/prod
   ```

3. Build and deploy frontend:
   ```bash
   cd frontend && npm run build
   # Deploy build/ folder to S3 + CloudFront
   ```

## 💡 Development Tips

- **API Server Logs**: Check terminal running `local-api-server.py` for processing details
- **Frontend Logs**: Open browser dev tools for React debugging
- **File Processing**: Check the temporary files created during upload processing
- **STARK Output**: The API server captures actual Rust program output

This gives you the complete ZK audit experience with real cryptographic operations, just running locally!