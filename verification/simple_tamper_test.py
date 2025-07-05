#!/usr/bin/env python3
"""
Simple tampering test - demonstrates real file tampering detection
"""

import os
import sys
import json
sys.path.append('.')
from verify_blocks import compute_sha3_hash, verify_merkle_path

def simple_tamper_test():
    print("🔍 SIMPLE TAMPERING TEST")
    print("=" * 40)
    
    # Use test blocks if available, otherwise use main commitment
    test_blocks_dir = '../test_blocks_commitments'
    main_blocks_dir = '../1_blocks_commitments'
    
    if os.path.exists(f'{test_blocks_dir}/merkle_commitment.json'):
        blocks_dir = test_blocks_dir
        commitment_file = f'{blocks_dir}/merkle_commitment.json'
        print("📁 Using test_blocks_commitments")
    else:
        blocks_dir = main_blocks_dir
        commitment_file = '../merkle_commitment.json'
        print("📁 Using main commitment (no block files to tamper)")
        
    # Load commitment
    with open(commitment_file, 'r') as f:
        commitment = json.load(f)
    
    first_block = commitment['block_metadata'][0]
    block_file = f"{blocks_dir}/{first_block['block_id']}.csv"
    
    print(f"📦 Testing block: {first_block['block_id']}")
    print(f"🔗 Committed hash: {first_block['hash']}")
    
    if not os.path.exists(block_file):
        print("❌ Block file not found - cannot test real tampering")
        print("💡 This test needs actual block files to modify")
        return
    
    # Read current file
    with open(block_file, 'rb') as f:
        current_content = f.read()
    
    current_hash = compute_sha3_hash(current_content)
    print(f"🔍 Current hash: {current_hash}")
    
    # Check if file matches commitment
    if current_hash == first_block['hash']:
        print("✅ File is INTACT (matches commitment)")
        
        # Now tamper with it
        print("\n🔧 TAMPERING WITH FILE...")
        tampered_content = current_content + b"\nTAMPERED_DATA_FOR_TEST"
        
        # Write tampered version temporarily
        with open(block_file, 'wb') as f:
            f.write(tampered_content)
        
        # Compute new hash
        tampered_hash = compute_sha3_hash(tampered_content)
        print(f"🔴 Tampered hash: {tampered_hash}")
        
        # Show difference
        diff_chars = sum(c1 != c2 for c1, c2 in zip(current_hash, tampered_hash))
        print(f"📊 Hash difference: {diff_chars}/{len(current_hash)} chars ({diff_chars/len(current_hash)*100:.1f}%)")
        
        # Test verification
        root_hash = commitment['root_hash'][0] if isinstance(commitment['root_hash'], list) else commitment['root_hash']
        auth_path = first_block['authentication_path']
        
        print(f"\n🔍 VERIFICATION TEST:")
        result = verify_merkle_path(tampered_hash, 0, auth_path, root_hash)
        print(f"Result: {'⚠️ NOT DETECTED' if result else '✅ TAMPERING DETECTED'}")
        
        # Restore original file
        print(f"\n🔄 Restoring original file...")
        with open(block_file, 'wb') as f:
            f.write(current_content)
        
        print("✅ File restored to original state")
        
    else:
        print("🔴 File is ALREADY MODIFIED!")
        print("   This means someone already tampered with it")
        print(f"   Expected: {first_block['hash']}")
        print(f"   Current:  {current_hash}")
        
        # Test verification with current (modified) hash
        root_hash = commitment['root_hash'][0] if isinstance(commitment['root_hash'], list) else commitment['root_hash']
        auth_path = first_block['authentication_path']
        
        print(f"\n🔍 VERIFICATION TEST:")
        result = verify_merkle_path(current_hash, 0, auth_path, root_hash)
        print(f"Result: {'⚠️ NOT DETECTED' if result else '✅ TAMPERING DETECTED'}")

def main():
    try:
        simple_tamper_test()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()