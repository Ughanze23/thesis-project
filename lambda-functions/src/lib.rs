// Lambda-compatible ZK audit system library
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use sha3::{Digest, Sha3_256};

// Re-export the STARK modules from the existing codebase
pub mod stark;

// Lambda event types
#[derive(Debug, Deserialize)]
pub struct BlockFetcherEvent {
    pub user_id: String,
    pub upload_id: String,
    pub selected_blocks: Vec<u32>,
    pub s3_bucket: String,
}

#[derive(Debug, Serialize)]
pub struct BlockFetcherResponse {
    pub audit_id: String,
    pub blocks_fetched: Vec<BlockData>,
    pub success: bool,
    pub error_message: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct HashGeneratorEvent {
    pub audit_id: String,
    pub blocks: Vec<BlockData>,
}

#[derive(Debug, Serialize)]
pub struct HashGeneratorResponse {
    pub audit_id: String,
    pub block_hashes: Vec<BlockHashData>,
    pub success: bool,
    pub error_message: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct StarkProverEvent {
    pub audit_id: String,
    pub block_hashes: Vec<BlockHashData>,
    pub merkle_commitment: MerkleCommitment,
}

#[derive(Debug, Serialize)]
pub struct StarkProverResponse {
    pub audit_id: String,
    pub stark_proofs: Vec<StarkProofData>,
    pub success: bool,
    pub error_message: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct StarkVerifierEvent {
    pub audit_id: String,
    pub stark_proofs: Vec<StarkProofData>,
    pub expected_root_hash: String,
}

#[derive(Debug, Serialize)]
pub struct StarkVerifierResponse {
    pub audit_id: String,
    pub verification_results: Vec<VerificationResult>,
    pub overall_success: bool,
    pub tampering_detected: bool,
    pub error_message: Option<String>,
}

// Data structures
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlockData {
    pub block_id: String,
    pub block_index: u32,
    pub s3_key: String,
    pub content: Option<String>, // CSV content
    pub size_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlockHashData {
    pub block_id: String,
    pub block_index: u32,
    pub hash: String,
    pub authentication_path: Vec<String>,
    pub size_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StarkProofData {
    pub block_id: String,
    pub block_index: u32,
    pub proof: SimpleStarkProof,
    pub generation_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerificationResult {
    pub block_id: String,
    pub block_index: u32,
    pub verification_passed: bool,
    pub verification_time_ms: u64,
    pub error_message: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct MerkleCommitment {
    pub commitment_type: String,
    pub hash_algorithm: String,
    pub root_hash: Vec<String>,
    pub total_blocks: usize,
    pub data_blocks: usize,
    pub empty_blocks: usize,
    pub blocks_power_of_2: bool,
    pub timestamp: String,
    pub block_metadata: Vec<BlockMetadata>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct BlockMetadata {
    pub block_id: String,
    pub hash: String,
    pub row_count: usize,
    pub size_bytes: usize,
    pub size_mb: f64,
    pub is_empty: bool,
    pub timestamp: String,
    pub authentication_path: Vec<String>,
}

// STARK proof structures (re-used from existing code)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimpleStarkProof {
    pub leaf_hash: String,
    pub root_hash: String,
    pub path_length: usize,
    pub execution_trace: Vec<TraceStep>,
    pub constraints: Vec<Constraint>,
    pub security_level: u32,
    pub proof_size_bytes: usize,
    pub generation_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceStep {
    pub step: usize,
    pub current_hash: String,
    pub sibling_hash: Option<String>,
    pub is_left_child: Option<bool>,
    pub parent_hash: Option<String>,
    pub operation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Constraint {
    pub constraint_type: String,
    pub step: usize,
    pub satisfied: bool,
    pub description: String,
}

// Utility functions
pub fn compute_sha3_hash(data: &[u8]) -> String {
    let mut hasher = Sha3_256::new();
    hasher.update(data);
    hex::encode(hasher.finalize())
}

pub fn compute_sha3_hash_str(data: &str) -> String {
    compute_sha3_hash(data.as_bytes())
}

// Error types for better Lambda error handling
#[derive(thiserror::Error, Debug)]
pub enum LambdaError {
    #[error("S3 error: {0}")]
    S3Error(String),
    
    #[error("DynamoDB error: {0}")]
    DynamoDbError(String),
    
    #[error("Hash computation error: {0}")]
    HashError(String),
    
    #[error("STARK proof error: {0}")]
    StarkError(String),
    
    #[error("Serialization error: {0}")]
    SerializationError(String),
    
    #[error("Invalid input: {0}")]
    InvalidInput(String),
}