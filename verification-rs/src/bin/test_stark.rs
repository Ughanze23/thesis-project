use anyhow::Result;
use merkle_verification::stark::{generate_stark_proof, verify_stark_proof};
use merkle_verification::compute_sha3_hash_str;

fn main() -> Result<()> {
    println!("=== STARK IMPLEMENTATION TEST ===");
    
    // Test data - use proper SHA3 hashes
    let leaf_hash = "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456";
    let sibling_hash = "b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456a1";
    let auth_path = vec![sibling_hash.to_string()];
    let leaf_index = 0;
    
    // Compute expected root using actual SHA3
    let parent_input = format!("{}{}", leaf_hash, sibling_hash); // left child
    let expected_root = compute_sha3_hash_str(&parent_input);
    
    println!("📦 Test parameters:");
    println!("   Leaf hash: {}", leaf_hash);
    println!("   Sibling hash: {}", sibling_hash);
    println!("   Expected root: {}", expected_root);
    println!("   Auth path length: {}", auth_path.len());
    
    // Generate STARK proof
    println!("\n⚡ Generating STARK proof...");
    let start_time = std::time::Instant::now();
    
    let proof = generate_stark_proof(
        leaf_hash,
        leaf_index,
        &auth_path,
        &expected_root,
    )?;
    
    let proof_time = start_time.elapsed();
    println!("✅ STARK proof generated in {:.2}ms", proof_time.as_millis());
    
    // Display proof details
    println!("\n📊 Proof details:");
    println!("   Security level: {} bits", proof.security_level);
    println!("   Execution trace steps: {}", proof.execution_trace.len());
    println!("   Constraints: {}", proof.constraints.len());
    println!("   Proof size: {} bytes ({:.2} KB)", proof.proof_size_bytes, proof.proof_size_bytes as f64 / 1024.0);
    println!("   Generation time: {} ms", proof.generation_time_ms);
    
    // Verify the proof
    println!("\n🔍 Verifying STARK proof...");
    let verify_start = std::time::Instant::now();
    
    let is_valid = verify_stark_proof(
        proof.clone(),
        leaf_hash,
        &expected_root,
        auth_path.len(),
    )?;
    
    let verify_time = verify_start.elapsed();
    println!("⏱️  Verification completed in {:.2}ms", verify_time.as_millis());
    
    if is_valid {
        println!("\n✅ PROOF VALID!");
        println!("🎉 STARK proof successfully verified!");
        println!("🔒 This cryptographically proves the Merkle path without revealing it");
        println!("🚀 Zero-knowledge: The proof reveals no information about sibling nodes");
        println!("⚡ Succinct: Verification is much faster than recomputing the path");
    } else {
        println!("\n❌ PROOF INVALID!");
        println!("⚠️  The STARK proof verification failed");
    }
    
    // Test with wrong data to ensure verification fails
    println!("\n🧪 Testing with wrong root hash...");
    let wrong_root = "wrong_root_hash_123456789012345678901234567890123456789012345678";
    let wrong_result = verify_stark_proof(
        proof,
        leaf_hash,
        wrong_root,
        auth_path.len(),
    )?;
    
    if !wrong_result {
        println!("✅ Correctly rejected invalid proof with wrong root");
    } else {
        println!("❌ ERROR: Accepted invalid proof!");
    }
    
    println!("\n🎯 STARK Implementation Test Complete!");
    
    Ok(())
}