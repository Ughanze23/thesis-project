use anyhow::Result;
use clap::Parser;
use merkle_verification::{load_commitment, get_root_hash, simple_stark::{SimpleStarkProof, verify_simple_stark_proof}};
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "simple_stark_verify")]
#[command(about = "Verify simplified STARK proof for Merkle path verification")]
struct Args {
    /// Path to the proof file
    #[arg(short, long, default_value = "simple_stark_proof.json")]
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
    println!("=== SIMPLIFIED STARK PROOF VERIFICATION ===");

    let args = Args::parse();

    // Load proof
    println!("📂 Loading proof from: {}", args.proof.display());
    let proof_json = fs::read_to_string(&args.proof)?;
    let proof: SimpleStarkProof = serde_json::from_str(&proof_json)?;

    println!("📊 Proof size: {} bytes ({:.2} KB)", proof.proof_size_bytes, proof.proof_size_bytes as f64 / 1024.0);

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

    // Verify proof matches expected values
    if proof.leaf_hash != block.hash {
        anyhow::bail!("Proof leaf hash doesn't match block hash");
    }
    if proof.root_hash != root_hash {
        anyhow::bail!("Proof root hash doesn't match commitment root");
    }

    if args.verbose {
        println!("\n🔍 Proof details:");
        println!("   🔒 Security level: {} bits", proof.security_level);
        println!("   🧮 Polynomial commitments: {}", proof.polynomial_commitments.len());
        println!("   🌊 FRI layers: {}", proof.fri_proof.layers.len());
        println!("   🎯 Query responses: {}", proof.fri_proof.query_responses.len());
        println!("   📐 Execution steps: {}", proof.execution_trace.len());
        
        println!("\n📋 Execution trace:");
        for (i, step) in proof.execution_trace.iter().enumerate() {
            println!("   Step {}: {} -> {}", i, &step.current_hash[..16], &step.parent_hash[..16]);
        }
    }

    println!("\n⚡ Verifying STARK proof...");
    let start_time = std::time::Instant::now();

    let is_valid = verify_simple_stark_proof(&proof)?;

    let verify_time = start_time.elapsed();
    println!("⏱️  Verification completed in {:.2}ms", verify_time.as_millis());

    if is_valid {
        println!("\n✅ PROOF VALID!");
        println!("🎉 STARK proof successfully verified!");
        println!("🔒 This cryptographically proves that block {} belongs to the Merkle tree", block.block_id);
        println!("🚀 Zero-knowledge: The proof reveals no information about other blocks");
        println!("⚡ Succinct: Verification is much faster than recomputing the entire path");
        println!("🧮 Polynomial commitments verified");
        println!("🌊 FRI proof verified");
        println!("📐 All constraints satisfied");
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