# Implementation

The zero-knowledge data integrity audit system is implemented using a distributed architecture with frontend, backend, and cryptographic verification components. This section details the technical implementation of each component and their integration.

## Frontend Implementation

The React-based frontend (`frontend/src/`) serves as the user interface for dataset management and audit configuration. Key components include:

### Upload Management (pages/UploadPage.tsx)
- File upload interface supporting CSV datasets up to 500MB
- Integration with FastAPI backend via multipart/form-data requests
- Real-time upload progress tracking and error handling
- Automatic dataset partitioning into manageable blocks

### Audit Configuration (pages/AuditPage.tsx)
- Interactive parameter selection for confidence levels (90-99%) and minimum corruption detection rates (1-20%)
- Statistical sample size calculation using the formula: `Math.log(failProb) / Math.log(1 - corruptionRate)`
- Real-time preview of audit parameters including sample size and detection probability

### Results Visualization (pages/ResultsPage.tsx)
- Comprehensive audit results display with block-level verification status
- Performance metrics visualization showing microsecond-level timing precision
- Privacy analysis comparing traditional vs zero-knowledge approaches
- Interactive charts for verification status distribution and timing analysis

## Backend Implementation

The FastAPI server (`fastapi-server.py`) orchestrates the entire audit pipeline through RESTful API endpoints:

### Core API Endpoints:
- `POST /api/upload`: Handles dataset upload, partitioning, and Merkle tree generation
- `POST /api/audit/start`: Initiates audit process with statistical sampling
- `GET /api/audit/{audit_id}/status`: Provides real-time audit status updates

### Statistical Sampling Algorithm:
```python
def calculate_sample_size(total_blocks, confidence_level, min_corruption_rate):
    fail_probability = 1 - (confidence_level / 100)
    theoretical_minimum = math.log(fail_probability) / math.log(1 - (min_corruption_rate / 100))
    return min(math.ceil(theoretical_minimum), total_blocks)
```

### Verification Orchestration:
The backend executes the Rust verification binary using subprocess calls:
```python
result = subprocess.run([
    "cargo", "run", "--bin", "verify_upload_blocks",
    upload_id, json.dumps(selected_blocks), commitment_path
], cwd="verification-rs/", capture_output=True, text=True)
```

## Cryptographic Verification System

The Rust-based verification system (`verification-rs/src/`) implements the core cryptographic protocols:

### Primary Verification Binary (bin/verify_upload_blocks.rs)
This binary performs the complete audit workflow:

#### 1. Data Integrity Verification:
- Computes SHA3-256 hashes of current block files
- Compares against stored commitment hashes to detect tampering
- Reports tampering with precise block identification

#### 2. Traditional Merkle Verification:
- Validates authentication paths against root hash
- Measures verification time in microseconds for performance analysis
- Serves as baseline for comparison with zero-knowledge approach

#### 3. STARK Proof Generation:
```rust
let prove_start = Instant::now();
let stark_proof = generate_stark_proof(
    &block.hash,
    block_index,
    &block.authentication_path,
    &root_hash,
)?;
let prove_time = prove_start.elapsed();
```

#### 4. Zero-Knowledge Verification:
```rust
let verify_start = Instant::now();
let zk_result = verify_stark_proof(
    stark_proof.clone(),
    &block.hash,
    &root_hash,
    block.authentication_path.len(),
)?;
let verify_time = verify_start.elapsed();
```

### STARK Implementation Details:
The system uses Scalable Transparent Arguments of Knowledge (STARKs) for zero-knowledge proofs:

- **Arithmetic Circuit Construction:** Merkle path verification is encoded as an arithmetic circuit over finite fields
- **Polynomial Commitment:** Uses FRI (Fast Reed-Solomon Interactive Oracle Proofs) for polynomial commitments
- **Security Parameters:** 128-bit security level with configurable proof sizes
- **Privacy Guarantee:** Zero sibling hashes revealed during verification process

## Performance Optimization

### Microsecond Timing Precision:
The implementation measures performance at microsecond granularity to capture sub-millisecond operations:
```rust
println!("✅ Traditional verification: PASSED ({:.1}μs)", traditional_time.as_micros());
println!("✅ STARK proof generated ({:.1}μs)", prove_time.as_micros());
println!("✅ Zero-knowledge verification: PASSED ({:.1}μs)", verify_time.as_micros());
```

### Frontend Display Logic:
The frontend intelligently displays timing based on magnitude:
```typescript
{result.verificationTimeMs && result.verificationTimeMs > 0 
  ? result.verificationTimeMs < 1 
    ? `${(result.verificationTimeMs * 1000).toFixed(0)}μs`
    : `${result.verificationTimeMs.toFixed(1)}ms`
  : '0μs'}
```

## Data Flow Architecture

### Upload and Commitment Phase:
1. User uploads CSV dataset through React frontend
2. FastAPI server partitions data into blocks and computes Merkle tree
3. Block metadata and authentication paths stored in JSON commitment file
4. Root hash serves as public commitment to dataset integrity

### Audit Execution Phase:
1. Frontend sends audit parameters to backend API
2. Backend calculates statistical sample using confidence parameters
3. Rust verification binary processes selected blocks independently
4. STARK proofs generated for each block with timing measurements
5. Results aggregated and returned via polling mechanism

### Privacy Preservation:
- Traditional verification would reveal `path_length × 32_bytes × num_blocks` of sibling hashes
- Zero-knowledge approach reveals zero bytes of authentication path data
- Privacy improvement quantified and reported in audit results

## Error Handling and Resilience

### Tampering Detection:
```rust
if current_hash != block.hash {
    println!("🚨 TAMPERING DETECTED! Block {} has been modified!", block_index);
    tampering_detected = true;
    verification_results.push((block_index, false, 0, 0, 0));
    continue;
}
```

### Frontend Polling Mechanism:
The frontend implements robust polling with error recovery:
```typescript
const pollAuditStatus = async () => {
  try {
    const statusData = await apiService.getAuditStatus(auditData.auditId);
    if (auditInfo.status === 'success' || auditInfo.status === 'failed') {
      // Process completion
      navigate(`/results/${auditData.auditId}`);
    } else {
      setTimeout(pollAuditStatus, 2000); // Continue polling
    }
  } catch (error) {
    actions.setError('Failed to get audit status');
  }
};
```

## Integration Architecture

### API Service Layer (frontend/src/services/api.ts)
The frontend communicates with the backend through a centralized API service:

```typescript
export const apiService = {
  async uploadDataset(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async startAudit(request: AuditStartRequest): Promise<AuditStartResponse> {
    const response = await api.post('/audit/start', request);
    return response.data;
  },

  async getAuditStatus(auditId: string) {
    const response = await api.get(`/audit/${auditId}/status`);
    return response.data.audit_data;
  }
};
```

### State Management
The frontend uses React Context for global state management:
- Upload tracking with duplicate prevention
- Audit status polling with real-time updates
- Error handling and user feedback

### File System Organization
```
verification-rs/src/bin/
├── verify_upload_blocks.rs  # Main verification binary
├── stark_prove.rs          # Standalone proof generation
└── stark_verify.rs         # Standalone proof verification
```

The `verify_upload_blocks.rs` binary is the only component called by the frontend system, while `stark_prove.rs` and `stark_verify.rs` serve as CLI tools for manual cryptographic operations.

## Security Implementation

### Input Validation
- File size limits (500MB) enforced at both frontend and backend
- JSON parsing with error handling for malformed block selections
- Path traversal protection for file access operations

### Cryptographic Security
- SHA3-256 for hash computations providing 256-bit security
- Secure random sampling using cryptographically secure PRNGs
- Constant-time operations where applicable to prevent timing attacks

### Error Propagation
The system implements comprehensive error handling:
```rust
let current_hash = match compute_block_file_hash(&block_file_path) {
    Ok(hash) => hash,
    Err(e) => {
        println!("❌ Failed to read block file {}: {}", block_file_path, e);
        continue;
    }
};
```

This implementation demonstrates a complete zero-knowledge audit system that achieves both cryptographic security and practical usability while maintaining complete privacy of authentication paths during verification.