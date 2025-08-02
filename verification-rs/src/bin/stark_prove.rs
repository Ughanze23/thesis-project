use anyhow::Result;
use clap::Parser;
use merkle_verification::{load_commitment, get_root_hash, stark::generate_stark_proof};
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "stark_prove")]
#[command(about = "Generate STARK proof for Merkle path verification")]
struct Args {
    /// Path to the merkle_commitment.json file
    #[arg(short, long, default_value = "../test_blocks_commitments/merkle_commitment.json")]
    commitment: PathBuf,

    /// Block index to prove (0-based)
    #[arg(short, long, default_value = "0")]
    block_index: usize,

    /// Output file for the proof
    #[arg(short, long, default_value = "merkle_proof.bin")]
    output: PathBuf,

    /// Enable verbose output
    #[arg(short, long)]
    verbose: bool,
}

fn main() -> Result<()> {
    println!("=== STARK PROOF GENERATION ===");

    let args = Args::parse();

    // Load commitment
    let commitment = load_commitment(&args.commitment)?;
    let root_hash = get_root_hash(&commitment);
    let blocks = &commitment.block_metadata;

    if args.block_index >= blocks.len() {
        anyhow::bail!("Block index {} out of range (max: {})", args.block_index, blocks.len() - 1);
    }

    let block = &blocks[args.block_index];
    
    println!("📦 Generating STARK proof for block: {}", block.block_id);
    println!("   Block hash: {}", block.hash);
    println!("   Root hash: {}", root_hash);
    println!("   Auth path length: {}", block.authentication_path.len());

    if args.verbose {
        println!("\n🔍 Authentication path:");
        for (i, hash) in block.authentication_path.iter().enumerate() {
            println!("   Level {}: {}", i + 1, hash);
        }
    }

    println!("\n⚡ Generating STARK proof...");
    let start_time = std::time::Instant::now();

    let proof = generate_stark_proof(
        &block.hash,
        args.block_index,
        &block.authentication_path,
        &root_hash,
    )?;

    let proof_time = start_time.elapsed();
    println!("✅ STARK proof generated in {:.2}s", proof_time.as_secs_f64());

    // Serialize and save proof
    let proof_bytes = bincode::serialize(&proof)
        .map_err(|e| anyhow::anyhow!("Failed to serialize proof: {}", e))?;
    
    fs::write(&args.output, &proof_bytes)?;
    
    println!("💾 Proof saved to: {}", args.output.display());
    println!("📊 Proof size: {} bytes ({:.2} KB)", proof_bytes.len(), proof_bytes.len() as f64 / 1024.0);

    println!("\n🎉 SUCCESS: STARK proof generated!");
    println!("🔒 This proof cryptographically demonstrates that block {} belongs to the Merkle tree", block.block_id);
    println!("📝 Use 'stark_verify' to verify this proof");

    Ok(())
}