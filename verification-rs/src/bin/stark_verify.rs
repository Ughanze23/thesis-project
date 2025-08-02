use anyhow::Result;
use clap::Parser;
use merkle_verification::{load_commitment, get_root_hash, stark::{verify_stark_proof, SimpleStarkProof}};
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "stark_verify")]
#[command(about = "Verify STARK proof for Merkle path verification")]
struct Args {
    /// Path to the proof file
    #[arg(short, long, default_value = "merkle_proof.bin")]
    proof: PathBuf,

    /// Path to the merkle_commitment.json file
    #[arg(short, long, default_value = "../test_blocks_commitments/merkle_commitment.json")]
    commitment: PathBuf,

    /// Block index that was proven (0-based)
    #[arg(short, long, default_value = "0")]
    block_index: usize,

    /// Enable verbose output
    #[arg(short, long)]
    verbose: bool,
}

fn main() -> Result<()> {
    println!("=== STARK PROOF VERIFICATION ===");

    let args = Args::parse();

    // Load proof
    println!("📂 Loading proof from: {}", args.proof.display());
    let proof_bytes = fs::read(&args.proof)?;
    let proof: SimpleStarkProof = bincode::deserialize(&proof_bytes)
        .map_err(|e| anyhow::anyhow!("Failed to deserialize proof: {}", e))?;

    println!("📊 Proof size: {} bytes ({:.2} KB)", proof_bytes.len(), proof_bytes.len() as f64 / 1024.0);

    // Load commitment
    let commitment = load_commitment(&args.commitment)?;
    let root_hash = get_root_hash(&commitment);
    let blocks = &commitment.block_metadata;

    if args.block_index >= blocks.len() {
        anyhow::bail!("Block index {} out of range (max: {})", args.block_index, blocks.len() - 1);
    }

    let block = &blocks[args.block_index];
    
    println!("📦 Verifying STARK proof for block: {}", block.block_id);
    println!("   Block hash: {}", block.hash);
    println!("   Root hash: {}", root_hash);
    println!("   Auth path length: {}", block.authentication_path.len());

    if args.verbose {
        println!("\n🔍 Proof details:");
        println!("   Trace length: {}", proof.execution_trace.len());
        println!("   Constraint count: {}", proof.constraints.len());
        println!("   Security level: {} bits", proof.security_level);
        println!("   Generation time: {} ms", proof.generation_time_ms);
    }

    println!("\n⚡ Verifying STARK proof...");
    let start_time = std::time::Instant::now();

    let is_valid = verify_stark_proof(
        proof,
        &block.hash,
        &root_hash,
        block.authentication_path.len(),
    )?;

    let verify_time = start_time.elapsed();
    println!("⏱️  Verification completed in {:.2}ms", verify_time.as_millis());

    if is_valid {
        println!("\n✅ PROOF VALID!");
        println!("🎉 STARK proof successfully verified!");
        println!("🔒 This cryptographically proves that block {} belongs to the Merkle tree", block.block_id);
        println!("🚀 Zero-knowledge: The proof reveals no information about other blocks");
    } else {
        println!("\n❌ PROOF INVALID!");
        println!("⚠️  The STARK proof verification failed");
        println!("🔍 This could indicate:");
        println!("   - Proof was tampered with");
        println!("   - Wrong block/commitment combination");
        println!("   - Proof generation error");
    }

    Ok(())
}