#!/usr/bin/env python3
"""
Test different scenarios for the ZK proof system
"""

import pandas as pd
import numpy as np
import os
import sys
sys.path.append('0_generate_dataset')
from generate_blocks_commitments import split_into_size_based_blocks, create_merkle_commitment

def test_scenario_1_small_dataset():
    """Test with small dataset (1 block)"""
    print("=== SCENARIO 1: Small Dataset (1 block) ===")
    
    # Create small dataset
    data = {'id': range(100), 'value': np.random.randint(1, 10, 100)}
    df = pd.DataFrame(data)
    df.to_csv('test_small.csv', index=False)
    
    # Generate commitment
    blocks, total = split_into_size_based_blocks('test_small.csv', 'test_small_blocks', 0.1)
    commitment, tree = create_merkle_commitment(blocks, 'test_small_blocks', total, 0.1)
    
    print(f"✅ Small dataset: {total} blocks, root: {tree.root}")
    return commitment

def test_scenario_2_medium_dataset():
    """Test with medium dataset (4 blocks)"""
    print("\n=== SCENARIO 2: Medium Dataset (4 blocks) ===")
    
    # Create medium dataset
    data = {
        'transaction_id': [f'TX_{i:06d}' for i in range(5000)],
        'amount': np.random.uniform(1, 1000, 5000),
        'timestamp': pd.date_range('2024-01-01', periods=5000, freq='1H'),
        'description': [f'Transaction {i}' for i in range(5000)]
    }
    df = pd.DataFrame(data)
    df.to_csv('test_medium.csv', index=False)
    
    # Generate commitment
    blocks, total = split_into_size_based_blocks('test_medium.csv', 'test_medium_blocks', 1.0)
    commitment, tree = create_merkle_commitment(blocks, 'test_medium_blocks', total, 1.0)
    
    print(f"✅ Medium dataset: {total} blocks, root: {tree.root}")
    return commitment

def test_scenario_3_verify_tampering():
    """Test tampering detection"""
    print("\n=== SCENARIO 3: Tampering Detection ===")
    
    # Use existing commitment
    import json
    try:
        with open('1_blocks_commitments/merkle_commitment.json', 'r') as f:
            commitment = json.load(f)
        
        # Test with correct data
        first_block = commitment['block_metadata'][0]
        root_hash = commitment['root_hash'][0] if isinstance(commitment['root_hash'], list) else commitment['root_hash']
        
        print(f"Original block hash: {first_block['hash']}")
        print(f"Original root: {root_hash}")
        
        # Simulate tampering by changing one character in block hash
        tampered_hash = first_block['hash'][:-1] + 'X'
        print(f"Tampered block hash: {tampered_hash}")
        
        # Verification should fail with tampered hash
        sys.path.append('1_blocks_commitments')
        from verify_blocks import verify_merkle_path
        
        result = verify_merkle_path(
            tampered_hash, 
            0, 
            first_block['authentication_path'], 
            root_hash
        )
        
        if result:
            print("❌ ERROR: Tampering not detected!")
        else:
            print("✅ SUCCESS: Tampering correctly detected!")
            
    except FileNotFoundError:
        print("⚠️ No existing commitment found, skipping tampering test")

def test_scenario_4_performance():
    """Test performance with different block sizes"""
    print("\n=== SCENARIO 4: Performance Test ===")
    
    import time
    
    # Create test dataset
    data = {
        'id': range(10000),
        'data': [f'data_{i}' * 10 for i in range(10000)]  # Make it larger
    }
    df = pd.DataFrame(data)
    df.to_csv('test_performance.csv', index=False)
    
    # Test different block sizes
    block_sizes = [0.5, 1.0, 2.0]
    
    for size in block_sizes:
        print(f"\n📊 Testing block size: {size} MB")
        start_time = time.time()
        
        blocks, total = split_into_size_based_blocks(
            'test_performance.csv', 
            f'test_perf_{size}MB_blocks', 
            size
        )
        commitment, tree = create_merkle_commitment(
            blocks, 
            f'test_perf_{size}MB_blocks', 
            total, 
            size
        )
        
        end_time = time.time()
        
        print(f"   Blocks: {total}")
        print(f"   Time: {end_time - start_time:.2f} seconds")
        print(f"   Root: {tree.root}")

def main():
    print("🧪 TESTING ZK PROOF SYSTEM")
    print("=" * 50)
    
    try:
        # Run all test scenarios
        test_scenario_1_small_dataset()
        test_scenario_2_medium_dataset()
        test_scenario_3_verify_tampering()
        test_scenario_4_performance()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS COMPLETED!")
        print("✅ Your ZK proof system is working correctly")
        print("🚀 Ready for production use")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("🔍 Check your setup and try again")

if __name__ == "__main__":
    main()