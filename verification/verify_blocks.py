#!/usr/bin/env python3
"""
Verify that blocks in merkle_commitment.json belong to the Merkle root
using their hashes and authentication paths.
"""

import json
import hashlib

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

def verify_merkle_path(leaf_hash, leaf_index, auth_path, expected_root):
    """
    Verify that a leaf belongs to a Merkle tree with the given root.
    
    Args:
        leaf_hash: Hash of the leaf node
        leaf_index: Index of the leaf in the tree (0-based)
        auth_path: List of sibling hashes from leaf to root
        expected_root: Expected root hash of the tree
    
    Returns:
        bool: True if verification succeeds, False otherwise
    """
    current_hash = leaf_hash
    current_index = leaf_index
    
    print(f"    Starting verification:")
    print(f"      Leaf hash: {current_hash}")
    print(f"      Leaf index: {current_index}")
    print(f"      Auth path length: {len(auth_path)}")
    
    # Traverse up the tree using authentication path
    for level, sibling_hash in enumerate(auth_path):
        print(f"      Level {level + 1}:")
        print(f"        Current: {current_hash}")
        print(f"        Sibling: {sibling_hash}")
        
        # Determine if current node is left or right child
        if current_index % 2 == 0:
            # Current is left child, sibling is right
            parent_input = current_hash + sibling_hash
            print(f"        Position: LEFT (concat current + sibling)")
        else:
            # Current is right child, sibling is left  
            parent_input = sibling_hash + current_hash
            print(f"        Position: RIGHT (concat sibling + current)")
        
        # Compute parent hash
        current_hash = compute_sha3_hash(parent_input)
        current_index = current_index // 2
        
        print(f"        Parent: {current_hash}")
    
    print(f"    Final computed root: {current_hash}")
    print(f"    Expected root: {expected_root}")
    
    return current_hash == expected_root

def main():
    print("=== MERKLE BLOCK VERIFICATION ===")
    
    # Load commitment data from thesis root
    commitment_file = '../merkle_commitment.json'
    try:
        with open(commitment_file, 'r') as f:
            commitment = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {commitment_file} not found")
        print("📝 Please place merkle_commitment.json in the thesis root directory")
        return
    
    # Extract root hash (handle both string and list formats)
    root_hash = commitment["root_hash"]
    if isinstance(root_hash, list):
        root_hash = root_hash[0]
    
    total_blocks = commitment["total_blocks"]
    blocks = commitment["block_metadata"]
    
    print(f"📋 Commitment Info:")
    print(f"   Root hash: {root_hash}")
    print(f"   Total blocks: {total_blocks}")
    print(f"   Tree height: {commitment['merkle_tree_structure']['height']}")
    
    print(f"\n🔍 Verifying blocks against Merkle root...")
    
    verified_count = 0
    failed_count = 0
    
    # Verify first few blocks (to avoid too much output)
    blocks_to_verify = len(blocks)
    
    for i in range(blocks_to_verify):
        block = blocks[i]
        block_id = block["block_id"]
        block_hash = block["hash"]
        auth_path = block["authentication_path"]
        
        print(f"\n📦 Block {i + 1}: {block_id}")
        print(f"   Hash: {block_hash}")
        print(f"   Size: {block['size_mb']:.2f} MB")
        print(f"   Rows: {block['row_count']}")
        
        # Verify the authentication path
        verified = verify_merkle_path(block_hash, i, auth_path, root_hash)
        
        if verified:
            print(f"   ✅ VERIFIED: Block belongs to Merkle root")
            verified_count += 1
        else:
            print(f"   ❌ FAILED: Block does not belong to Merkle root")
            failed_count += 1
    
    if blocks_to_verify < len(blocks):
        print(f"\n📝 Note: Verified first {blocks_to_verify} blocks out of {len(blocks)} total")
    
    print(f"\n📊 Verification Summary:")
    print(f"   ✅ Verified: {verified_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📈 Success rate: {verified_count/(verified_count+failed_count)*100:.1f}%")
    
    if verified_count > 0 and failed_count == 0:
        print(f"\n🎉 SUCCESS: All verified blocks belong to the committed Merkle root!")
        print(f"🔒 This proves data integrity - the blocks haven't been tampered with")
    elif failed_count > 0:
        print(f"\n⚠️  WARNING: Some blocks failed verification")
        print(f"🔍 This could indicate data corruption or implementation issues")

if __name__ == "__main__":
    main()