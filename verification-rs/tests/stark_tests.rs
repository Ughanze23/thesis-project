use anyhow::Result;
use merkle_verification::stark::{generate_stark_proof, verify_stark_proof, SimpleStarkProof};
use merkle_verification::{compute_sha3_hash_str, load_commitment, get_root_hash};

#[test]
fn test_stark_proof_generation_and_verification() -> Result<()> {
    // Simple test case
    let leaf_hash = "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456";
    let sibling_hash = "b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456a1";
    let auth_path = vec![sibling_hash.to_string()];
    let leaf_index = 0;
    
    // Compute expected root using SHA3
    let parent_input = format!("{}{}", leaf_hash, sibling_hash);
    let expected_root = compute_sha3_hash_str(&parent_input);
    
    // Generate proof
    let proof = generate_stark_proof(leaf_hash, leaf_index, &auth_path, &expected_root)?;
    
    // Verify proof structure
    assert_eq!(proof.leaf_hash, leaf_hash);
    assert_eq!(proof.root_hash, expected_root);
    assert_eq!(proof.path_length, 1);
    assert_eq!(proof.security_level, 128);
    assert!(!proof.execution_trace.is_empty());
    assert!(!proof.constraints.is_empty());
    
    // Verify proof
    let is_valid = verify_stark_proof(proof, leaf_hash, &expected_root, auth_path.len())?;
    assert!(is_valid);
    
    Ok(())
}

#[test]
fn test_stark_proof_with_wrong_root() -> Result<()> {
    let leaf_hash = "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456";
    let sibling_hash = "b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456a1";
    let auth_path = vec![sibling_hash.to_string()];
    let leaf_index = 0;
    
    let parent_input = format!("{}{}", leaf_hash, sibling_hash);
    let expected_root = compute_sha3_hash_str(&parent_input);
    
    // Generate valid proof
    let proof = generate_stark_proof(leaf_hash, leaf_index, &auth_path, &expected_root)?;
    
    // Try to verify with wrong root
    let wrong_root = "wrong_root_hash_123456789012345678901234567890123456789012345678";
    let is_valid = verify_stark_proof(proof, leaf_hash, wrong_root, auth_path.len())?;
    assert!(!is_valid);
    
    Ok(())
}

#[test]
fn test_stark_proof_with_wrong_leaf() -> Result<()> {
    let leaf_hash = "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456";
    let sibling_hash = "b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456a1";
    let auth_path = vec![sibling_hash.to_string()];
    let leaf_index = 0;
    
    let parent_input = format!("{}{}", leaf_hash, sibling_hash);
    let expected_root = compute_sha3_hash_str(&parent_input);
    
    // Generate valid proof
    let proof = generate_stark_proof(leaf_hash, leaf_index, &auth_path, &expected_root)?;
    
    // Try to verify with wrong leaf
    let wrong_leaf = "wrong_leaf_hash_123456789012345678901234567890123456789012345678";
    let is_valid = verify_stark_proof(proof, wrong_leaf, &expected_root, auth_path.len())?;
    assert!(!is_valid);
    
    Ok(())
}

#[test]
fn test_stark_proof_multi_level() -> Result<()> {
    // Test with 3-level tree (2 authentication path elements)
    let leaf_hash = "leaf_hash_123456789012345678901234567890123456789012345678901234";
    let sibling1 = "sibling1_hash_123456789012345678901234567890123456789012345678901";
    let sibling2 = "sibling2_hash_123456789012345678901234567890123456789012345678901";
    let auth_path = vec![sibling1.to_string(), sibling2.to_string()];
    let leaf_index = 0; // Left child at each level
    
    // Compute expected root
    let level1_input = format!("{}{}", leaf_hash, sibling1);
    let level1_hash = compute_sha3_hash_str(&level1_input);
    let level2_input = format!("{}{}", level1_hash, sibling2);
    let expected_root = compute_sha3_hash_str(&level2_input);
    
    // Generate and verify proof
    let proof = generate_stark_proof(leaf_hash, leaf_index, &auth_path, &expected_root)?;
    assert_eq!(proof.path_length, 2);
    assert_eq!(proof.execution_trace.len(), 3); // Initial + 2 levels
    
    let is_valid = verify_stark_proof(proof, leaf_hash, &expected_root, auth_path.len())?;
    assert!(is_valid);
    
    Ok(())
}

#[test]
fn test_stark_proof_right_child() -> Result<()> {
    // Test with leaf as right child
    let leaf_hash = "leaf_hash_123456789012345678901234567890123456789012345678901234";
    let sibling_hash = "sibling_hash_123456789012345678901234567890123456789012345678901";
    let auth_path = vec![sibling_hash.to_string()];
    let leaf_index = 1; // Right child
    
    // Compute expected root (sibling + leaf for right child)
    let parent_input = format!("{}{}", sibling_hash, leaf_hash);
    let expected_root = compute_sha3_hash_str(&parent_input);
    
    // Generate and verify proof
    let proof = generate_stark_proof(leaf_hash, leaf_index, &auth_path, &expected_root)?;
    let is_valid = verify_stark_proof(proof, leaf_hash, &expected_root, auth_path.len())?;
    assert!(is_valid);
    
    Ok(())
}

#[test]
fn test_stark_proof_serialization() -> Result<()> {
    let leaf_hash = "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456";
    let sibling_hash = "b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456a1";
    let auth_path = vec![sibling_hash.to_string()];
    let leaf_index = 0;
    
    let parent_input = format!("{}{}", leaf_hash, sibling_hash);
    let expected_root = compute_sha3_hash_str(&parent_input);
    
    // Generate proof
    let original_proof = generate_stark_proof(leaf_hash, leaf_index, &auth_path, &expected_root)?;
    
    // Serialize and deserialize
    let serialized = bincode::serialize(&original_proof)?;
    let deserialized_proof: SimpleStarkProof = bincode::deserialize(&serialized)?;
    
    // Verify deserialized proof
    assert_eq!(original_proof.leaf_hash, deserialized_proof.leaf_hash);
    assert_eq!(original_proof.root_hash, deserialized_proof.root_hash);
    assert_eq!(original_proof.path_length, deserialized_proof.path_length);
    
    let is_valid = verify_stark_proof(deserialized_proof, leaf_hash, &expected_root, auth_path.len())?;
    assert!(is_valid);
    
    Ok(())
}

#[test]
fn test_stark_proof_performance() -> Result<()> {
    let leaf_hash = "performance_test_leaf_hash_123456789012345678901234567890123456";
    let sibling_hash = "performance_test_sibling_hash_123456789012345678901234567890123";
    let auth_path = vec![sibling_hash.to_string()];
    let leaf_index = 0;
    
    let parent_input = format!("{}{}", leaf_hash, sibling_hash);
    let expected_root = compute_sha3_hash_str(&parent_input);
    
    // Measure proof generation time
    let start = std::time::Instant::now();
    let proof = generate_stark_proof(leaf_hash, leaf_index, &auth_path, &expected_root)?;
    let proof_time = start.elapsed();
    
    // Measure verification time
    let start = std::time::Instant::now();
    let is_valid = verify_stark_proof(proof.clone(), leaf_hash, &expected_root, auth_path.len())?;
    let verify_time = start.elapsed();
    
    assert!(is_valid);
    
    // Performance assertions (should be very fast for simple cases)
    assert!(proof_time.as_millis() < 100, "Proof generation took too long: {}ms", proof_time.as_millis());
    assert!(verify_time.as_millis() < 50, "Verification took too long: {}ms", verify_time.as_millis());
    
    // Proof size should be reasonable
    assert!(proof.proof_size_bytes < 2000, "Proof size too large: {} bytes", proof.proof_size_bytes);
    
    Ok(())
}

#[cfg(test)]
mod integration_tests {
    use super::*;
    use std::path::PathBuf;
    
    #[test]
    fn test_stark_proof_with_real_commitment() -> Result<()> {
        // Try to load real commitment file
        let commitment_path = PathBuf::from("../test_blocks_commitments/merkle_commitment.json");
        
        if !commitment_path.exists() {
            // Skip test if commitment file doesn't exist
            println!("Skipping integration test - commitment file not found");
            return Ok(());
        }
        
        let commitment = load_commitment(&commitment_path)?;
        let root_hash = get_root_hash(&commitment);
        let blocks = &commitment.block_metadata;
        
        if blocks.is_empty() {
            println!("Skipping integration test - no blocks in commitment");
            return Ok(());
        }
        
        // Test with first block
        let block = &blocks[0];
        let proof = generate_stark_proof(
            &block.hash,
            0,
            &block.authentication_path,
            &root_hash,
        )?;
        
        let is_valid = verify_stark_proof(
            proof,
            &block.hash,
            &root_hash,
            block.authentication_path.len(),
        )?;
        
        assert!(is_valid);
        
        Ok(())
    }
}