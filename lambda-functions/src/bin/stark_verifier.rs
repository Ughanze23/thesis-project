// Lambda function: STARK Verifier
// Verifies ZK-STARK proofs to detect tampering

use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use std::time::Instant;
use tracing::{info, error, warn};
use zk_audit_lambda::{
    StarkVerifierEvent, StarkVerifierResponse, VerificationResult,
    stark::verify_stark_proof, LambdaError
};

async fn function_handler(event: LambdaEvent<StarkVerifierEvent>) -> Result<StarkVerifierResponse, Error> {
    let (event, _context) = event.into_parts();
    
    info!("Processing STARK proof verification for audit: {}", event.audit_id);
    info!("Number of proofs to verify: {}", event.stark_proofs.len());
    info!("Expected root hash: {}", event.expected_root_hash);
    
    let mut verification_results = Vec::new();
    let mut errors = Vec::new();
    let mut tampering_detected = false;
    
    // Verify each STARK proof
    for proof_data in &event.stark_proofs {
        info!("Verifying STARK proof for block: {}", proof_data.block_id);
        
        let start_time = Instant::now();
        
        match verify_block_stark_proof(proof_data, &event.expected_root_hash).await {
            Ok(passed) => {
                let verification_time_ms = start_time.elapsed().as_millis() as u64;
                
                if !passed {
                    tampering_detected = true;
                    warn!("TAMPERING DETECTED for block: {} (verification failed)", proof_data.block_id);
                } else {
                    info!("STARK proof verification PASSED for block: {} (took {}ms)", 
                          proof_data.block_id, verification_time_ms);
                }
                
                verification_results.push(VerificationResult {
                    block_id: proof_data.block_id.clone(),
                    block_index: proof_data.block_index,
                    verification_passed: passed,
                    verification_time_ms,
                    error_message: None,
                });
            }
            Err(e) => {
                error!("Failed to verify STARK proof for block {}: {}", proof_data.block_id, e);
                errors.push(format!("Block {}: {}", proof_data.block_id, e));
                
                verification_results.push(VerificationResult {
                    block_id: proof_data.block_id.clone(),
                    block_index: proof_data.block_index,
                    verification_passed: false,
                    verification_time_ms: start_time.elapsed().as_millis() as u64,
                    error_message: Some(e.to_string()),
                });
            }
        }
    }
    
    let overall_success = errors.is_empty() && !tampering_detected;
    let error_message = if errors.is_empty() {
        None
    } else {
        Some(errors.join("; "))
    };
    
    // Summary logging
    let passed_count = verification_results.iter().filter(|r| r.verification_passed).count();
    let failed_count = verification_results.len() - passed_count;
    
    info!("STARK proof verification completed:");
    info!("  Total proofs: {}", verification_results.len());
    info!("  Passed: {}", passed_count);
    info!("  Failed: {}", failed_count);
    info!("  Tampering detected: {}", tampering_detected);
    info!("  Overall success: {}", overall_success);
    
    if tampering_detected {
        warn!("🚨 DATA TAMPERING DETECTED - Some blocks failed verification");
    } else {
        info!("✅ All blocks verified successfully - No tampering detected");
    }
    
    Ok(StarkVerifierResponse {
        audit_id: event.audit_id,
        verification_results,
        overall_success,
        tampering_detected,
        error_message,
    })
}

async fn verify_block_stark_proof(
    proof_data: &zk_audit_lambda::StarkProofData, 
    expected_root_hash: &str
) -> Result<bool, LambdaError> {
    
    info!("Verifying STARK proof for block {} (index {}) with {} trace steps", 
          proof_data.block_id, 
          proof_data.block_index,
          proof_data.proof.execution_trace.len());
    
    // Extract the leaf hash from the proof
    let leaf_hash = &proof_data.proof.leaf_hash;
    
    // Verify the STARK proof
    let verification_result = verify_stark_proof(
        &proof_data.proof,
        leaf_hash,
        expected_root_hash,
    ).map_err(|e| {
        error!("STARK proof verification failed for block {}: {}", proof_data.block_id, e);
        e
    })?;
    
    if verification_result {
        info!("STARK proof verification PASSED for block {}", proof_data.block_id);
    } else {
        warn!("STARK proof verification FAILED for block {} - TAMPERING DETECTED", proof_data.block_id);
        info!("  Expected root: {}", expected_root_hash);
        info!("  Proof root: {}", proof_data.proof.root_hash);
        info!("  Leaf hash: {}", leaf_hash);
    }
    
    Ok(verification_result)
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .with_target(false)
        .without_time()
        .init();

    info!("Starting STARK Verifier Lambda function");
    
    run(service_fn(function_handler)).await
}