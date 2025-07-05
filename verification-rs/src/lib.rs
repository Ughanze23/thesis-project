use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use sha3::{Digest, Sha3_256};
use std::fs;
use std::path::Path;

// STARK implementation modules
pub mod simple_stark;
pub mod stark;

#[derive(Debug, Deserialize, Serialize)]
pub struct MerkleCommitment {
    pub commitment_type: String,
    pub hash_algorithm: String,
    pub root_hash: Vec<String>,
    pub total_blocks: usize,
    pub data_blocks: usize,
    pub empty_blocks: usize,
    pub blocks_power_of_2: bool,
    pub target_block_size_mb: f64,
    pub timestamp: String,
    pub block_metadata: Vec<BlockMetadata>,
    pub merkle_tree_structure: Option<MerkleTreeStructure>,
    pub size_statistics: Option<SizeStatistics>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct BlockMetadata {
    pub block_id: String,
    pub hash: String,
    pub row_count: usize,
    pub size_bytes: usize,
    pub size_mb: f64,
    pub is_empty: bool,
    pub timestamp: String,
    pub authentication_path: Vec<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct MerkleTreeStructure {
    pub height: usize,
    pub leaf_count: usize,
    pub is_complete_binary_tree: bool,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct SizeStatistics {
    pub total_size_mb: f64,
    pub data_size_mb: f64,
    pub average_block_size_mb: f64,
    pub min_block_size_mb: f64,
    pub max_block_size_mb: f64,
}

pub fn compute_sha3_hash(data: &[u8]) -> String {
    let mut hasher = Sha3_256::new();
    hasher.update(data);
    hex::encode(hasher.finalize())
}

pub fn compute_sha3_hash_str(data: &str) -> String {
    compute_sha3_hash(data.as_bytes())
}

pub fn verify_merkle_path(
    leaf_hash: &str,
    leaf_index: usize,
    auth_path: &[String],
    expected_root: &str,
    verbose: bool,
) -> Result<bool> {
    let mut current_hash = leaf_hash.to_string();
    let mut current_index = leaf_index;

    if verbose {
        println!("    Starting verification:");
        println!("      Leaf hash: {}", current_hash);
        println!("      Leaf index: {}", current_index);
        println!("      Auth path length: {}", auth_path.len());
    }

    // Traverse up the tree using authentication path
    for (level, sibling_hash) in auth_path.iter().enumerate() {
        if verbose {
            println!("      Level {}:", level + 1);
            println!("        Current: {}", current_hash);
            println!("        Sibling: {}", sibling_hash);
        }

        // Determine if current node is left or right child
        let parent_input = if current_index % 2 == 0 {
            // Current is left child, sibling is right
            if verbose {
                println!("        Position: LEFT (concat current + sibling)");
            }
            format!("{}{}", current_hash, sibling_hash)
        } else {
            // Current is right child, sibling is left
            if verbose {
                println!("        Position: RIGHT (concat sibling + current)");
            }
            format!("{}{}", sibling_hash, current_hash)
        };

        // Compute parent hash
        current_hash = compute_sha3_hash_str(&parent_input);
        current_index /= 2;

        if verbose {
            println!("        Parent: {}", current_hash);
        }
    }

    if verbose {
        println!("    Final computed root: {}", current_hash);
        println!("    Expected root: {}", expected_root);
    }

    Ok(current_hash == expected_root)
}

pub fn load_commitment<P: AsRef<Path>>(path: P) -> Result<MerkleCommitment> {
    let content = fs::read_to_string(path).context("Failed to read commitment file")?;
    let commitment: MerkleCommitment =
        serde_json::from_str(&content).context("Failed to parse commitment JSON")?;
    Ok(commitment)
}

pub fn get_root_hash(commitment: &MerkleCommitment) -> String {
    // Handle both string and list formats
    commitment.root_hash[0].clone()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sha3_hash() {
        let input = "hello world";
        let expected = "644bcc7e564373040999aac89e7622f3ca71fba1d972fd94a31c3bfbf24e3938";
        assert_eq!(compute_sha3_hash_str(input), expected);
    }

    #[test]
    fn test_merkle_verification_simple() {
        // Simple 2-leaf tree test
        let leaf_hash = "a";
        let sibling_hash = "b";
        let auth_path = vec![sibling_hash.to_string()];
        
        // Expected root should be hash of "ab"
        let expected_root = compute_sha3_hash_str("ab");
        
        let result = verify_merkle_path(leaf_hash, 0, &auth_path, &expected_root, false);
        assert!(result.unwrap());
    }
}