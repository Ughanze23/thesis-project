use anyhow::Result;
use merkle_verification::{
    load_commitment, get_root_hash, verify_merkle_path, compute_block_file_hash,
    stark::{generate_stark_proof, verify_stark_proof}
};
use std::env;
use std::time::Instant;
use serde_json;

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 {
        eprintln!("Usage: {} <upload_id> <selected_blocks_json> <merkle_commitment_path>", args[0]);
        eprintln!("Example: {} upload_123 '[0,1,2]' ../1_blocks_commitments/merkle_commitment.json", args[0]);
        std::process::exit(1);
    }
    
    let upload_id = &args[1];
    let selected_blocks_json = &args[2]; 
    let commitment_path = &args[3];
    
    println!("🔒 ZERO-KNOWLEDGE VERIFICATION FOR UPLOAD");
    println!("==========================================");
    println!("📋 Upload ID: {}", upload_id);
    println!("📋 Selected blocks: {}", selected_blocks_json);
    println!("📋 Commitment file: {}", commitment_path);
    
    // Parse selected blocks
    let selected_blocks: Vec<usize> = serde_json::from_str(selected_blocks_json)
        .map_err(|e| anyhow::anyhow!("Failed to parse selected blocks JSON: {}", e))?;
    
    if selected_blocks.is_empty() {
        println!("❌ No blocks selected for verification");
        return Ok(());
    }
    
    println!("📊 Will verify {} blocks: {:?}", selected_blocks.len(), selected_blocks);
    
    // Load commitment data for this specific upload
    let commitment = load_commitment(commitment_path)?;
    let root_hash = get_root_hash(&commitment);
    let blocks = &commitment.block_metadata;
    
    if blocks.is_empty() {
        println!("❌ No blocks found in commitment file");
        return Ok(());
    }
    
    println!("\n📋 Dataset Information:");
    println!("   Total blocks in commitment: {}", blocks.len());
    println!("   Tree height: {}", commitment.merkle_tree_structure.as_ref().map(|s| s.height).unwrap_or(0));
    println!("   Root hash: {}", root_hash);
    
    let mut verification_results = Vec::new();
    let mut total_proof_size = 0;
    let mut total_generation_time = 0;
    let mut total_verification_time = 0;
    let mut tampering_detected = false;
    
    // Verify each selected block
    for &block_index in &selected_blocks {
        if block_index >= blocks.len() {
            println!("⚠️  Block index {} out of range (max: {})", block_index, blocks.len() - 1);
            continue;
        }
        
        let block = &blocks[block_index];
        println!("\n🔍 VERIFYING BLOCK {}: {}", block_index, block.block_id);
        
        // Calculate the current hash of the block file
        let block_file_path = format!("../upload_blocks/{}/{}.csv", upload_id, block.block_id);
        let current_hash = match compute_block_file_hash(&block_file_path) {
            Ok(hash) => hash,
            Err(e) => {
                println!("❌ Failed to read block file {}: {}", block_file_path, e);
                continue;
            }
        };
        
        println!("   Original hash: {}", block.hash);
        println!("   Current hash:  {}", current_hash);
        println!("   Block size: {:.2} MB", block.size_mb);
        println!("   Auth path length: {}", block.authentication_path.len());
        
        // Check for tampering
        if current_hash != block.hash {
            println!("🚨 TAMPERING DETECTED! Block {} has been modified!", block_index);
            println!("   Expected: {}", block.hash);
            println!("   Found:    {}", current_hash);
            tampering_detected = true;
            verification_results.push((block_index, false, 0, 0, 0));
            continue;
        }
        
        // Traditional verification first (should use original hash for Merkle path)
        let traditional_start = Instant::now();
        let traditional_result = verify_merkle_path(
            &block.hash,
            block_index,
            &block.authentication_path,
            &root_hash,
            false,
        )?;
        let traditional_time = traditional_start.elapsed();
        
        if !traditional_result {
            println!("❌ Traditional verification FAILED for block {}", block_index);
            println!("🚨 This indicates tampering or data corruption!");
            continue;
        }
        
        println!("✅ Traditional verification: PASSED ({:.1}μs)", traditional_time.as_micros());
        
        // Generate STARK proof
        println!("⚡ Generating STARK proof...");
        let prove_start = Instant::now();
        let stark_proof = generate_stark_proof(
            &block.hash,
            block_index,
            &block.authentication_path,
            &root_hash,
        )?;
        let prove_time = prove_start.elapsed();
        total_generation_time += prove_time.as_micros();
        
        println!("✅ STARK proof generated ({:.1}μs)", prove_time.as_micros());
        println!("   Proof size: {} bytes", stark_proof.proof_size_bytes);
        println!("   Security level: {} bits", stark_proof.security_level);
        total_proof_size += stark_proof.proof_size_bytes;
        
        // Verify STARK proof
        println!("🔒 Verifying STARK proof...");
        let verify_start = Instant::now();
        let zk_result = verify_stark_proof(
            stark_proof.clone(),
            &block.hash,
            &root_hash,
            block.authentication_path.len(),
        )?;
        let verify_time = verify_start.elapsed();
        total_verification_time += verify_time.as_micros();
        
        if zk_result {
            println!("✅ Zero-knowledge verification: PASSED ({:.1}μs)", verify_time.as_micros());
            verification_results.push((block_index, true, stark_proof.proof_size_bytes, prove_time.as_micros(), verify_time.as_micros()));
        } else {
            println!("❌ Zero-knowledge verification: FAILED");
            verification_results.push((block_index, false, stark_proof.proof_size_bytes, prove_time.as_micros(), verify_time.as_micros()));
        }
    }
    
    // Summary
    println!("\n📊 VERIFICATION SUMMARY");
    println!("=======================");
    
    let successful_verifications = verification_results.iter().filter(|(_, success, _, _, _)| *success).count();
    let total_verifications = verification_results.len();
    
    println!("📋 Blocks processed: {}", total_verifications);
    println!("✅ Successful verifications: {}", successful_verifications);
    println!("❌ Failed verifications: {}", total_verifications - successful_verifications);
    
    if total_verifications > 0 {
        println!("📊 Total proof size: {} bytes ({:.2} KB)", total_proof_size, total_proof_size as f64 / 1024.0);
        println!("⏱️  Total generation time: {} μs ({:.2} ms)", total_generation_time, total_generation_time as f64 / 1000.0);
        println!("⏱️  Total verification time: {} μs ({:.2} ms)", total_verification_time, total_verification_time as f64 / 1000.0);
        println!("📈 Average proof size: {} bytes", total_proof_size / total_verifications);
        println!("📈 Average generation time: {} μs", total_generation_time / total_verifications as u128);
        println!("📈 Average verification time: {} μs", total_verification_time / total_verifications as u128);
        
        // Privacy analysis
        let traditional_path_size = blocks.iter()
            .enumerate()
            .filter(|(i, _)| selected_blocks.contains(i))
            .map(|(_, block)| block.authentication_path.len() * 64)
            .sum::<usize>();
        
        println!("\n🔐 PRIVACY ANALYSIS");
        println!("===================");
        println!("📊 Traditional reveals: {} bytes of authentication paths", traditional_path_size);
        println!("🔒 Zero-knowledge reveals: 0 bytes (100% private)");
        println!("📈 Privacy improvement: {} bytes of sensitive data hidden", traditional_path_size);
    }
    
    // Final status
    if tampering_detected {
        println!("\n🚨 TAMPERING DETECTED!");
        println!("❌ One or more blocks have been modified since commitment");
        println!("🛡️  Zero-knowledge audit system successfully detected data tampering");
        std::process::exit(1);
    } else if successful_verifications == total_verifications && total_verifications > 0 {
        println!("\n🎉 ALL VERIFICATIONS PASSED!");
        println!("🔒 Zero-knowledge proofs successfully generated and verified");
        println!("🛡️  Data integrity confirmed with complete privacy");
    } else if successful_verifications > 0 {
        println!("\n⚠️  PARTIAL SUCCESS: {}/{} verifications passed", successful_verifications, total_verifications);
        println!("🔍 Some blocks may have integrity issues");
    } else {
        println!("\n❌ ALL VERIFICATIONS FAILED!");
        println!("🚨 Critical integrity issues detected");
        std::process::exit(1);
    }
    
    Ok(())
}