// Lambda function: STARK Prover
// Generates ZK-STARK proofs for block membership

use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use std::time::Instant;
use tracing::{info, error};
use zk_audit_lambda::{
    StarkProverEvent, StarkProverResponse, StarkProofData,
    stark::generate_stark_proof, LambdaError
};

async fn function_handler(event: LambdaEvent<StarkProverEvent>) -> Result<StarkProverResponse, Error> {
    let (event, _context) = event.into_parts();
    
    info!("Processing STARK proof generation for audit: {}", event.audit_id);
    info!("Number of blocks to prove: {}", event.block_hashes.len());
    
    // Extract root hash from commitment
    let root_hash = event.merkle_commitment.root_hash.first()
        .ok_or_else(|| LambdaError::InvalidInput("Root hash not found in commitment".to_string()))?;
    
    info!("Using root hash: {}", root_hash);
    
    let mut stark_proofs = Vec::new();
    let mut errors = Vec::new();
    
    // Generate STARK proof for each block
    for block_hash in &event.block_hashes {
        info!("Generating STARK proof for block: {}", block_hash.block_id);
        
        let start_time = Instant::now();
        
        match generate_block_stark_proof(block_hash, root_hash).await {
            Ok(mut proof_data) => {
                proof_data.generation_time_ms = start_time.elapsed().as_millis() as u64;
                let generation_time = proof_data.generation_time_ms;
                stark_proofs.push(proof_data);
                info!("Successfully generated STARK proof for block: {} (took {}ms)", 
                      block_hash.block_id, generation_time);
            }
            Err(e) => {
                error!("Failed to generate STARK proof for block {}: {}", block_hash.block_id, e);
                errors.push(format!("Block {}: {}", block_hash.block_id, e));
            }
        }
    }
    
    let success = errors.is_empty();
    let error_message = if errors.is_empty() {
        None
    } else {
        Some(errors.join("; "))
    };
    
    info!("STARK proof generation completed: {} proofs generated, {} errors", 
          stark_proofs.len(), errors.len());
    
    Ok(StarkProverResponse {
        audit_id: event.audit_id,
        stark_proofs,
        success,
        error_message,
    })
}

async fn generate_block_stark_proof(
    block_hash: &zk_audit_lambda::BlockHashData, 
    root_hash: &str
) -> Result<StarkProofData, LambdaError> {
    
    info!("Generating STARK proof for block {} with hash {}", 
          block_hash.block_id, &block_hash.hash[..16]);
    
    // Generate the STARK proof
    let proof = generate_stark_proof(
        &block_hash.hash,
        block_hash.block_index as usize,
        &block_hash.authentication_path,
        root_hash,
    ).map_err(|e| {
        error!("STARK proof generation failed: {}", e);
        e
    })?;
    
    info!("STARK proof generated successfully for block {}: {} bytes, {} trace steps", 
          block_hash.block_id, proof.proof_size_bytes, proof.execution_trace.len());
    
    Ok(StarkProofData {
        block_id: block_hash.block_id.clone(),
        block_index: block_hash.block_index,
        proof,
        generation_time_ms: 0, // Will be set by caller
    })
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .with_target(false)
        .without_time()
        .init();

    info!("Starting STARK Prover Lambda function");
    
    run(service_fn(function_handler)).await
}