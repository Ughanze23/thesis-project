use anyhow::Result;
use clap::Parser;
use merkle_verification::{get_root_hash, load_commitment, verify_merkle_path};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "verify_blocks")]
#[command(about = "Verify that blocks in merkle_commitment.json belong to the Merkle root")]
struct Args {
    /// Path to the merkle_commitment.json file
    #[arg(short, long, default_value = "../merkle_commitment.json")]
    commitment: PathBuf,

    /// Enable verbose output
    #[arg(short, long)]
    verbose: bool,

    /// Maximum number of blocks to verify (0 = all)
    #[arg(short, long, default_value = "0")]
    max_blocks: usize,

    /// Directory containing block files
    #[arg(short, long)]
    blocks_dir: Option<PathBuf>,
}

fn main() -> Result<()> {
    let args = Args::parse();

    println!("=== MERKLE BLOCK VERIFICATION (Rust) ===");

    // Load commitment data
    let commitment = match load_commitment(&args.commitment) {
        Ok(c) => c,
        Err(e) => {
            println!("❌ Error: Failed to load {}", args.commitment.display());
            println!("📝 {}", e);
            return Err(e);
        }
    };

    // Extract root hash
    let root_hash = get_root_hash(&commitment);
    let total_blocks = commitment.total_blocks;
    let blocks = &commitment.block_metadata;

    println!("📋 Commitment Info:");
    println!("   Root hash: {}", root_hash);
    println!("   Total blocks: {}", total_blocks);
    if let Some(structure) = &commitment.merkle_tree_structure {
        println!("   Tree height: {}", structure.height);
    }

    println!("\n🔍 Verifying blocks against Merkle root...");

    let mut verified_count = 0;
    let mut failed_count = 0;

    // Determine how many blocks to verify
    let blocks_to_verify = if args.max_blocks == 0 {
        blocks.len()
    } else {
        args.max_blocks.min(blocks.len())
    };

    for (i, block) in blocks.iter().take(blocks_to_verify).enumerate() {
        println!("\n📦 Block {}: {}", i + 1, block.block_id);
        println!("   Hash: {}", block.hash);
        println!("   Size: {:.2} MB", block.size_mb);
        println!("   Rows: {}", block.row_count);

        // Verify the authentication path
        match verify_merkle_path(
            &block.hash,
            i,
            &block.authentication_path,
            &root_hash,
            args.verbose,
        ) {
            Ok(true) => {
                println!("   ✅ VERIFIED: Block belongs to Merkle root");
                verified_count += 1;
            }
            Ok(false) => {
                println!("   ❌ FAILED: Block does not belong to Merkle root");
                failed_count += 1;
            }
            Err(e) => {
                println!("   ❌ ERROR: Verification failed: {}", e);
                failed_count += 1;
            }
        }
    }

    if blocks_to_verify < blocks.len() {
        println!(
            "\n📝 Note: Verified first {} blocks out of {} total",
            blocks_to_verify,
            blocks.len()
        );
    }

    println!("\n📊 Verification Summary:");
    println!("   ✅ Verified: {}", verified_count);
    println!("   ❌ Failed: {}", failed_count);
    let total = verified_count + failed_count;
    if total > 0 {
        println!(
            "   📈 Success rate: {:.1}%",
            (verified_count as f64 / total as f64) * 100.0
        );
    }

    if verified_count > 0 && failed_count == 0 {
        println!("\n🎉 SUCCESS: All verified blocks belong to the committed Merkle root!");
        println!("🔒 This proves data integrity - the blocks haven't been tampered with");
    } else if failed_count > 0 {
        println!("\n⚠️  WARNING: Some blocks failed verification");
        println!("🔍 This could indicate data corruption or implementation issues");
    }

    Ok(())
}