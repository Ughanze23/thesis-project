import os
import pandas as pd
import hashlib
import json
import math
from tqdm import tqdm
from datetime import datetime

def compute_sha3_hash(data):
    """Compute SHA-3 hash of input data."""
    hasher = hashlib.sha3_256()
    if isinstance(data, str):
        hasher.update(data.encode('utf-8'))
    elif isinstance(data, bytes):
        hasher.update(data)
    else:
        hasher.update(str(data).encode('utf-8'))
    return hasher.hexdigest()

class MerkleTree:
    """Simple Merkle Tree implementation for block commitments."""
    
    def __init__(self, leaves):
        """Initialize Merkle tree with leaf hashes."""
        self.leaves = leaves
        self.tree = self._build_tree(leaves)
        self.root = self.tree[0] if self.tree else None
        self.leaf_count = len(leaves)
    
    def _build_tree(self, leaves):
        """Build the Merkle tree from leaf nodes."""
        if not leaves:
            return []
        
        # Since we ensure power of 2 blocks, no need to pad
        tree = [leaves]  # Level 0: leaves
        current_level = leaves
        
        # Build tree bottom-up
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1]
                parent_hash = compute_sha3_hash(left + right)
                next_level.append(parent_hash)
            
            tree.insert(0, next_level)  # Insert at beginning to have root at index 0
            current_level = next_level
        
        return tree
    
    def get_authentication_path_hashes(self, leaf_index):
        """Get authentication path as list of sibling hashes needed to verify the leaf."""
        if leaf_index >= self.leaf_count or not self.tree:
            return []
        
        auth_path_hashes = []
        current_index = leaf_index
        
        # Start from the bottom level (leaves) and work up
        for level in range(len(self.tree) - 1, 0, -1):
            current_level_nodes = self.tree[level]
            
            # Find sibling index at this level
            if current_index % 2 == 0:
                sibling_index = current_index + 1
            else:
                sibling_index = current_index - 1
            
            # Add sibling hash if it exists
            if sibling_index < len(current_level_nodes):
                auth_path_hashes.append(current_level_nodes[sibling_index])
            
            # Move to parent level
            current_index = current_index // 2
        
        return auth_path_hashes

def split_into_size_based_blocks(input_file, output_dir, target_block_size_mb=2):
    """Split CSV file into blocks of target size, ensuring power of 2 total blocks."""
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get file size
    file_size = os.path.getsize(input_file)
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"Input file size: {file_size_mb:.2f} MB")
    
    # Calculate number of blocks needed for target size
    estimated_blocks = math.ceil(file_size_mb / target_block_size_mb)
    
    # Round UP to nearest power of 2
    power_of_2_blocks = 2 ** math.ceil(math.log2(estimated_blocks))
    
    # Keep original target block size (2MB)
    target_block_size_bytes = int(target_block_size_mb * 1024 * 1024)
    
    print(f"Blocks needed for {target_block_size_mb}MB each: {estimated_blocks}")
    print(f"Rounded up to power of 2: {power_of_2_blocks} blocks")
    print(f"Block size: {target_block_size_mb} MB ({target_block_size_bytes:,} bytes)")

    # Read CSV file
    df = pd.read_csv(input_file)
    total_rows = len(df)
    
    print(f"Total rows: {total_rows:,}")
    print(f"Creating {power_of_2_blocks} blocks...")

    block_metadata = []
    current_row = 0
    
    # Split into size-based blocks
    for block_index in range(power_of_2_blocks):
        block_file = os.path.join(output_dir, f"block_{block_index + 1:04d}.csv")
        
        if current_row >= total_rows:
            # Create empty block if we've used all data
            block_data = pd.DataFrame(columns=df.columns)
        else:
            # Estimate rows needed to reach target size
            sample_size = min(100, total_rows - current_row)
            sample_data = df.iloc[current_row:current_row + sample_size]
            sample_csv = sample_data.to_csv(index=False)
            bytes_per_row = len(sample_csv.encode('utf-8')) / sample_size
            
            target_rows = max(1, int(target_block_size_bytes / bytes_per_row))
            end_row = min(current_row + target_rows, total_rows)
            
            block_data = df.iloc[current_row:end_row]
            current_row = end_row
        
        # Save block
        block_data.to_csv(block_file, index=False)
        
        # Compute block hash and metadata
        with open(block_file, 'rb') as f:
            block_content = f.read()
            block_hash = compute_sha3_hash(block_content)
        
        block_size = len(block_content)
        
        metadata = {
            "block_id": f"block_{block_index + 1:04d}",
            "hash": block_hash,
            "row_count": len(block_data),
            "size_bytes": block_size,
            "size_mb": block_size / (1024 * 1024),
            "is_empty": len(block_data) == 0,
            "timestamp": datetime.now().isoformat()
        }
        
        block_metadata.append(metadata)
        
        status = "EMPTY" if metadata['is_empty'] else ""
        print(f"Created {metadata['block_id']}: {metadata['row_count']} rows, "
              f"{metadata['size_mb']:.2f} MB, hash: {block_hash[:16]}... {status}")

    return block_metadata, power_of_2_blocks

def create_merkle_commitment(block_metadata, output_dir, total_blocks, target_block_size_mb):
    """Create Merkle tree commitment from block metadata."""
    print("\nBuilding Merkle tree commitment...")
    
    # Extract block hashes in order
    block_hashes = [block['hash'] for block in block_metadata]
    
    # Verify we have power of 2 blocks
    assert len(block_hashes) == total_blocks
    assert (total_blocks & (total_blocks - 1)) == 0, "Total blocks must be power of 2"
    
    # Build Merkle tree
    merkle_tree = MerkleTree(block_hashes)
    
    # Generate authentication paths for each block
    print("Generating authentication paths...")
    for i, block in enumerate(block_metadata):
        auth_path_hashes = merkle_tree.get_authentication_path_hashes(i)
        block['authentication_path'] = auth_path_hashes
        print(f"Block {block['block_id']}: {len(auth_path_hashes)} sibling hashes")
    
    expected_path_length = int(math.log2(total_blocks))
    print(f"Expected authentication path length: {expected_path_length} hashes per block")
    
    # Count non-empty blocks
    non_empty_blocks = [block for block in block_metadata if not block.get('is_empty', False)]
    empty_blocks = len(block_metadata) - len(non_empty_blocks)
    
    # Create commitment data
    commitment_data = {
        "commitment_type": "merkle_tree",
        "hash_algorithm": "SHA3-256",
        "root_hash": merkle_tree.root,
        "total_blocks": len(block_metadata),
        "data_blocks": len(non_empty_blocks),
        "empty_blocks": empty_blocks,
        "blocks_power_of_2": True,
        "target_block_size_mb": target_block_size_mb,
        "timestamp": datetime.now().isoformat(),
        "block_metadata": block_metadata,
        "merkle_tree_structure": {
            "height": len(merkle_tree.tree),
            "leaf_count": len(block_hashes),
            "is_complete_binary_tree": True
        },
        "size_statistics": {
            "total_size_mb": sum(block['size_mb'] for block in block_metadata),
            "data_size_mb": sum(block['size_mb'] for block in non_empty_blocks),
            "average_block_size_mb": sum(block['size_mb'] for block in non_empty_blocks) / len(non_empty_blocks) if non_empty_blocks else 0,
            "min_block_size_mb": min((block['size_mb'] for block in non_empty_blocks), default=0),
            "max_block_size_mb": max((block['size_mb'] for block in non_empty_blocks), default=0)
        }
    }
    
    # Save commitment
    commitment_file = os.path.join(output_dir, 'merkle_commitment.json')
    with open(commitment_file, 'w') as f:
        json.dump(commitment_data, f, indent=4)
    
    print(f"Merkle commitment saved to: {commitment_file}")
    print(f"Merkle Root: {merkle_tree.root}")
    print(f"Tree Height: {len(merkle_tree.tree)}")
    
    return commitment_data, merkle_tree

def main():
    # Get input parameters
    input_file = input("Enter the path to the input CSV file: ")
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} does not exist.")
    
    output_dir = input("Enter the directory to save blocks and commitments: ")
    
    # Get target block size (with default)
    size_input = input("Enter target block size in MB (default 2): ").strip()
    target_size_mb = float(size_input) if size_input else 2.0
    
    print(f"\nProcessing with target block size of {target_size_mb} MB...")
    print("Note: Total blocks will be rounded up to power of 2, last block may be smaller")
    
    # Step 1: Split into size-based blocks
    block_metadata, total_blocks = split_into_size_based_blocks(input_file, output_dir, target_size_mb)
    
    # Step 2: Create Merkle tree commitment
    commitment_data, merkle_tree = create_merkle_commitment(block_metadata, output_dir, total_blocks, target_size_mb)
    
    # Summary
    stats = commitment_data['size_statistics']
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Hash algorithm: SHA3-256")
    print(f"Total blocks created: {len(block_metadata)} (power of 2: ✓)")
    print(f"Data blocks: {commitment_data['data_blocks']}")
    print(f"Empty blocks: {commitment_data['empty_blocks']}")
    print(f"Target block size: {target_size_mb} MB")
    print(f"Total data size: {stats['data_size_mb']:.2f} MB")
    print(f"Average data block size: {stats['average_block_size_mb']:.2f} MB")
    print(f"Data block size range: {stats['min_block_size_mb']:.2f} - {stats['max_block_size_mb']:.2f} MB")
    print(f"Merkle tree height: {len(merkle_tree.tree)}")
    print(f"Authentication paths: Generated for all blocks")
    print(f"Merkle root: {merkle_tree.root}")
    
    # Verify power of 2
    print(f"Power of 2 verification: {total_blocks} = 2^{int(math.log2(total_blocks))}")

if __name__ == "__main__":
    main()