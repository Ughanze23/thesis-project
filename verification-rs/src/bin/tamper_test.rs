use anyhow::{Context, Result};
use clap::Parser;
use merkle_verification::{compute_sha3_hash, get_root_hash, load_commitment, verify_merkle_path};
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "tamper_test")]
#[command(about = "Test tamper detection by modifying a block file and verifying it fails")]
struct Args {
    /// Path to the merkle_commitment.json file
    #[arg(short, long, default_value = "../test_blocks_commitments/merkle_commitment.json")]
    commitment: PathBuf,

    /// Block file to test (e.g., block_0001.csv)
    #[arg(short, long, default_value = "../test_blocks_commitments/block_0001.csv")]
    block_file: PathBuf,

    /// Block index in the commitment (0-based)
    #[arg(short, long, default_value = "0")]
    index: usize,

    /// Enable verbose output
    #[arg(short, long)]
    verbose: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();

    println!("=== TAMPER DETECTION TEST (Rust) ===");
    println!("🧪 Testing cryptographic integrity verification");

    // Load commitment
    let commitment = load_commitment(&args.commitment)
        .context("Failed to load commitment file")?;

    let root_hash = get_root_hash(&commitment);
    let blocks = &commitment.block_metadata;

    if args.index >= blocks.len() {
        println!("❌ Error: Block index {} out of range (max: {})", args.index, blocks.len() - 1);
        return Ok(());
    }

    let block = &blocks[args.index];
    println!("\n📦 Testing block: {}", block.block_id);
    println!("   Expected hash: {}", block.hash);
    println!("   File: {}", args.block_file.display());

    // Step 1: Verify original file
    println!("\n🔍 Step 1: Verify original file integrity");
    
    let original_content = fs::read(&args.block_file)
        .context("Failed to read block file")?;
    
    let computed_hash = compute_sha3_hash(&original_content);
    println!("   Computed hash: {}", computed_hash);
    
    if computed_hash == block.hash {
        println!("   ✅ Original file hash matches commitment");
    } else {
        println!("   ❌ Original file hash does NOT match commitment");
        println!("   🔍 This indicates the file may already be modified");
    }

    // Verify against Merkle root
    let original_verified = verify_merkle_path(
        &computed_hash,
        args.index,
        &block.authentication_path,
        &root_hash,
        args.verbose,
    )?;

    if original_verified {
        println!("   ✅ Original file verifies against Merkle root");
    } else {
        println!("   ❌ Original file does NOT verify against Merkle root");
    }

    // Step 2: Create backup and modify file
    println!("\n🔧 Step 2: Modify file to test tamper detection");
    
    let backup_path = args.block_file.with_extension("csv.backup");
    fs::copy(&args.block_file, &backup_path)
        .context("Failed to create backup")?;
    println!("   📋 Created backup: {}", backup_path.display());

    // Read original content and modify it
    let original_text = fs::read_to_string(&args.block_file)
        .context("Failed to read file as text")?;
    
    // Simple modification: change first occurrence of a digit
    let modified_text = if let Some(pos) = original_text.find(char::is_numeric) {
        let mut chars: Vec<char> = original_text.chars().collect();
        let original_char = chars[pos];
        let new_char = if original_char == '9' { '0' } else { 
            char::from_digit(original_char.to_digit(10).unwrap() + 1, 10).unwrap()
        };
        chars[pos] = new_char;
        println!("   🔄 Changed '{}' to '{}' at position {}", original_char, new_char, pos);
        chars.into_iter().collect()
    } else {
        // Fallback: append a character
        println!("   🔄 Appended 'X' to end of file");
        format!("{}X", original_text)
    };

    fs::write(&args.block_file, &modified_text)
        .context("Failed to write modified file")?;

    // Step 3: Verify modified file fails
    println!("\n🔍 Step 3: Verify modified file fails verification");
    
    let modified_content = fs::read(&args.block_file)
        .context("Failed to read modified file")?;
    
    let modified_hash = compute_sha3_hash(&modified_content);
    println!("   Modified hash: {}", modified_hash);
    
    // Calculate hash difference
    let original_bytes = hex::decode(&block.hash).unwrap_or_default();
    let modified_bytes = hex::decode(&modified_hash).unwrap_or_default();
    let mut different_bits = 0;
    
    for (orig, modif) in original_bytes.iter().zip(modified_bytes.iter()) {
        different_bits += (orig ^ modif).count_ones();
    }
    
    let total_bits = original_bytes.len() * 8;
    let change_percentage = if total_bits > 0 {
        (different_bits as f64 / total_bits as f64) * 100.0
    } else {
        0.0
    };
    
    println!("   📊 Hash changed: {:.1}% of bits ({}/{})", 
             change_percentage, different_bits, total_bits);

    if modified_hash != block.hash {
        println!("   ✅ Hash changed as expected (tamper detected)");
    } else {
        println!("   ❌ Hash unchanged (this should not happen!)");
    }

    // Verify against Merkle root
    let modified_verified = verify_merkle_path(
        &modified_hash,
        args.index,
        &block.authentication_path,
        &root_hash,
        args.verbose,
    )?;

    if !modified_verified {
        println!("   ✅ Modified file FAILS Merkle verification (tamper detected)");
    } else {
        println!("   ❌ Modified file still verifies (this should not happen!)");
    }

    // Step 4: Restore original file
    println!("\n🔄 Step 4: Restore original file");
    
    fs::copy(&backup_path, &args.block_file)
        .context("Failed to restore from backup")?;
    fs::remove_file(&backup_path)
        .context("Failed to remove backup")?;
    
    println!("   ✅ Original file restored");

    // Final verification
    let restored_content = fs::read(&args.block_file)
        .context("Failed to read restored file")?;
    let restored_hash = compute_sha3_hash(&restored_content);
    
    if restored_hash == block.hash {
        println!("   ✅ Restored file hash matches original");
    } else {
        println!("   ❌ Restored file hash does not match original");
    }

    // Summary
    println!("\n📊 Tamper Detection Summary:");
    println!("   🔒 Original verification: {}", if original_verified { "✅ PASS" } else { "❌ FAIL" });
    println!("   🚨 Tamper detection: {}", if !modified_verified { "✅ DETECTED" } else { "❌ MISSED" });
    println!("   📈 Hash change: {:.1}%", change_percentage);
    
    if original_verified && !modified_verified {
        println!("\n🎉 SUCCESS: Tamper detection working correctly!");
        println!("🔒 Any modification to the data is cryptographically detectable");
    } else {
        println!("\n⚠️  WARNING: Tamper detection may not be working correctly");
    }

    Ok(())
}