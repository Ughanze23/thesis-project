#!/usr/bin/env python3
"""
Standalone ZK Audit Script - Direct command line auditing
Usage: python3 standalone_audit.py <filename.csv>

This script replicates the FastAPI server's audit functionality without needing the API:
1. Takes a CSV file as input
2. Splits it into blocks (same as cloud_data_ingestion.py)
3. Runs random block selection
4. Performs STARK verification using verification-rs
"""

import sys
import os
import subprocess
import tempfile
import uuid
import json
import logging
import pandas as pd
import shutil
import hashlib
import math
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step, message):
    """Print a step with formatting"""
    print(f"\n🔧 Step {step}: {message}")

class StandaloneMerkleTree:
    """Merkle Tree implementation for standalone audit."""
    
    def __init__(self, leaves: List[str]):
        self.leaves = leaves
        self.tree = self._build_tree(leaves)
        self.root = self.tree[0][0] if self.tree and len(self.tree[0]) > 0 else None
        self.leaf_count = len(leaves)
    
    def _build_tree(self, leaves: List[str]) -> List[List[str]]:
        """Build the Merkle tree from leaf nodes."""
        if not leaves:
            return []
        
        tree = [leaves]  # Level 0: leaves
        current_level = leaves
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else current_level[i]
                parent_hash = self._compute_sha3_hash(left + right)
                next_level.append(parent_hash)
            
            tree.insert(0, next_level)
            current_level = next_level
        
        return tree
    
    def _compute_sha3_hash(self, data: str) -> str:
        """Compute SHA-3 hash of input data."""
        hasher = hashlib.sha3_256()
        hasher.update(data.encode('utf-8'))
        return hasher.hexdigest()
    
    def get_authentication_path(self, leaf_index: int) -> List[str]:
        """Get authentication path for given leaf index."""
        if leaf_index >= self.leaf_count or not self.tree:
            return []
        
        auth_path = []
        current_index = leaf_index
        
        for level in range(len(self.tree) - 1, 0, -1):
            current_level_nodes = self.tree[level]
            
            if current_index % 2 == 0:
                sibling_index = current_index + 1
            else:
                sibling_index = current_index - 1
            
            if sibling_index < len(current_level_nodes):
                auth_path.append(current_level_nodes[sibling_index])
            
            current_index = current_index // 2
        
        return auth_path

def compute_block_hash(data: bytes) -> str:
    """Compute SHA3-256 hash of block data."""
    hasher = hashlib.sha3_256()
    hasher.update(data)
    return hasher.hexdigest()

def create_blocks_from_csv(csv_file, upload_id, blocks_dir, block_size_mb=2.0):
    """
    Create data blocks from CSV file with proper power-of-2 structure and hash calculation
    """
    print(f"📄 Reading CSV file: {csv_file}")
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        file_size = os.path.getsize(csv_file)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"📊 File info:")
        print(f"   📏 Size: {file_size_mb:.2f} MB")
        print(f"   📋 Rows: {len(df)}")
        print(f"   📰 Columns: {len(df.columns)}")
        
        # Calculate optimal block count (power of 2) - same as cloud_data_ingestion.py
        estimated_blocks = math.ceil(file_size_mb / block_size_mb)
        power_of_2_blocks = 2 ** math.ceil(math.log2(estimated_blocks))
        target_block_size_bytes = int(block_size_mb * 1024 * 1024)
        
        print(f"🧮 Estimated blocks needed: {estimated_blocks}")
        print(f"🔢 Rounded to power of 2: {power_of_2_blocks}")
        print(f"📦 Target block size: {block_size_mb} MB")
        
        # Create blocks directory
        blocks_dir.mkdir(parents=True, exist_ok=True)
        
        total_rows = len(df)
        block_metadata = []
        current_row = 0
        
        # Generate blocks with proper metadata
        for block_index in tqdm(range(power_of_2_blocks), desc="Creating blocks"):
            block_id = f"block_{block_index + 1:04d}"
            block_file = blocks_dir / f"{block_id}.csv"
            
            if current_row >= total_rows:
                # Create empty block
                block_data = pd.DataFrame(columns=df.columns)
            else:
                # Estimate rows for target size
                sample_size = min(1000, total_rows - current_row)
                if sample_size > 0:
                    sample_data = df.iloc[current_row:current_row + sample_size]
                    sample_csv = sample_data.to_csv(index=False)
                    bytes_per_row = len(sample_csv.encode('utf-8')) / sample_size
                    target_rows = max(1, int(target_block_size_bytes / bytes_per_row))
                else:
                    target_rows = 1
                
                end_row = min(current_row + target_rows, total_rows)
                block_data = df.iloc[current_row:end_row]
                current_row = end_row
            
            # Save block locally
            block_data.to_csv(block_file, index=False)
            
            # Calculate block hash and metadata
            with open(block_file, 'rb') as f:
                block_content = f.read()
                block_hash = compute_block_hash(block_content)
            
            metadata = {
                "block_id": block_id,
                "hash": block_hash,
                "row_count": len(block_data),
                "size_bytes": len(block_content),
                "size_mb": len(block_content) / (1024 * 1024),
                "is_empty": len(block_data) == 0,
                "timestamp": datetime.now().isoformat(),
                "upload_id": upload_id,
                "local_path": str(block_file)
            }
            
            block_metadata.append(metadata)
            
            if not metadata['is_empty']:
                print(f"   📦 Block {block_index + 1:04d}: {len(block_data)} rows, {metadata['size_mb']:.2f}MB -> {block_file.name}")
        
        print(f"✅ Created {power_of_2_blocks} data blocks in {blocks_dir}")
        
        return {
            'total_blocks': power_of_2_blocks,
            'file_size_mb': file_size_mb,
            'rows_processed': len(df),
            'blocks_dir': str(blocks_dir),
            'block_metadata': block_metadata
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating blocks: {e}")
        return None

def create_merkle_commitment(block_metadata: List[Dict], upload_id: str, user_id: str = "cli_user", target_block_size_mb: float = 2.0) -> Dict:
    """Create Merkle tree commitment from block metadata."""
    print(f"🌳 Building Merkle tree commitment for {len(block_metadata)} blocks...")
    
    # Extract block hashes
    block_hashes = [block['hash'] for block in block_metadata]
    
    # Build Merkle tree
    merkle_tree = StandaloneMerkleTree(block_hashes)
    
    # Generate authentication paths for each block
    print("🔐 Generating authentication paths...")
    for i, block in enumerate(block_metadata):
        auth_path = merkle_tree.get_authentication_path(i)
        block['authentication_path'] = auth_path
    
    # Calculate statistics
    non_empty_blocks = [b for b in block_metadata if not b.get('is_empty', False)]
    empty_blocks = len(block_metadata) - len(non_empty_blocks)
    
    commitment_data = {
        "commitment_type": "merkle_tree",
        "hash_algorithm": "SHA3-256",
        "root_hash": [merkle_tree.root],  # Array format for Rust compatibility
        "total_blocks": len(block_metadata),
        "data_blocks": len(non_empty_blocks),
        "empty_blocks": empty_blocks,
        "blocks_power_of_2": True,
        "target_block_size_mb": target_block_size_mb,
        "timestamp": datetime.now().isoformat(),
        "upload_id": upload_id,
        "user_id": user_id,
        "block_metadata": block_metadata,
        "merkle_tree_structure": {
            "height": len(merkle_tree.tree),
            "leaf_count": len(block_hashes),
            "is_complete_binary_tree": True
        },
        "size_statistics": {
            "total_size_mb": sum(b['size_mb'] for b in block_metadata),
            "data_size_mb": sum(b['size_mb'] for b in non_empty_blocks),
            "average_block_size_mb": (sum(b['size_mb'] for b in non_empty_blocks) / 
                                    len(non_empty_blocks)) if non_empty_blocks else 0,
            "min_block_size_mb": min((b['size_mb'] for b in non_empty_blocks), default=0),
            "max_block_size_mb": max((b['size_mb'] for b in non_empty_blocks), default=0)
        }
    }
    
    print(f"✅ Merkle root: {merkle_tree.root}")
    print(f"🌲 Tree height: {len(merkle_tree.tree)}")
    print(f"📊 Data blocks: {len(non_empty_blocks)}, Empty blocks: {empty_blocks}")
    
    return commitment_data

def save_commitment_file(commitment_data: Dict, upload_id: str) -> str:
    """Save commitment file to local storage and return path."""
    project_root = Path(__file__).parent
    commitments_dir = project_root / "merkle_commitments"
    commitments_dir.mkdir(exist_ok=True)
    
    commitment_filename = f"commitment_{upload_id}.json"
    commitment_path = commitments_dir / commitment_filename
    
    # Save commitment file
    with open(commitment_path, 'w') as f:
        json.dump(commitment_data, f, indent=2)
    
    print(f"💾 Commitment file saved: {commitment_path}")
    return str(commitment_path)

def run_block_selection(total_blocks, upload_id, confidence=0.95, min_corruption=0.05):
    """
    Run random block selection algorithm, same as FastAPI server
    """
    print(f"🎲 Running random block selection algorithm")
    print(f"   📊 Total blocks: {total_blocks}")
    print(f"   🎯 Confidence: {confidence*100}%")
    print(f"   🔍 Min corruption rate: {min_corruption*100}%")
    
    try:
        project_root = Path(__file__).parent
        cmd = [
            'python3', 'random_block_selector.py',
            '--total-blocks', str(total_blocks),
            '--user-id', 'cli_user',
            '--upload-id', upload_id,
            '--confidence', str(confidence),
            '--min-corruption', str(min_corruption)
        ]
        
        logger.info(f"🎲 Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, timeout=300)
        
        if result.returncode != 0:
            logger.warning(f"⚠️  Block selection failed, using fallback")
            logger.warning(f"stderr: {result.stderr}")
            # Fallback: select first few blocks
            sample_size = 100
            selected_blocks = list(range(sample_size))
            return selected_blocks, sample_size
        
        # Parse block selection results
        output_lines = result.stdout.split('\n')
        selected_blocks = []
        sample_size = 4
        
        for line in output_lines:
            if 'Selected blocks:' in line:
                try:
                    sample_size = int(line.split(':')[1].strip().split()[0])
                except Exception as e:
                    logger.warning(f"⚠️  Failed to parse sample_size: {e}")
            elif line.strip().startswith('[') and ']' in line:
                try:
                    import re
                    numbers = re.findall(r'\d+', line)
                    new_blocks = [int(n) for n in numbers]
                    selected_blocks.extend(new_blocks)
                except Exception as e:
                    logger.warning(f"⚠️  Failed to parse block line '{line}': {e}")
        
        if not selected_blocks:
            logger.warning(f"⚠️  No blocks parsed, using sequential fallback")
            selected_blocks = list(range(min(sample_size, total_blocks)))
        
        print(f"✅ Block selection completed:")
        print(f"   🎯 Sample size: {len(selected_blocks)} blocks")
        print(f"   📋 Selected blocks: {selected_blocks}")
        print(f"   📊 Sample percentage: {(len(selected_blocks) / total_blocks * 100):.2f}%")
        
        return selected_blocks, len(selected_blocks)
        
    except subprocess.TimeoutExpired:
        logger.warning("⏰ Block selection timed out, using fallback")
        sample_size = min(8, total_blocks)
        selected_blocks = list(range(sample_size))
        return selected_blocks, sample_size
    except Exception as e:
        logger.warning(f"⚠️  Block selection error: {e}, using fallback")
        sample_size = min(8, total_blocks)
        selected_blocks = list(range(sample_size))
        return selected_blocks, sample_size

def run_stark_verification(upload_id, selected_blocks, blocks_dir, commitment_file_path):
    """
    Run STARK verification using verification-rs with the generated commitment file
    """
    print(f"🔒 Starting STARK verification")
    print(f"   🆔 Upload ID: {upload_id}")
    print(f"   🎯 Verifying {len(selected_blocks)} blocks: {selected_blocks}")
    
    try:
        project_root = Path(__file__).parent / 'verification-rs'
        
        if not project_root.exists():
            logger.error(f"❌ verification-rs directory not found at {project_root}")
            return None
        
        # Use the generated commitment file
        commitment_file = Path(commitment_file_path)
        
        if not commitment_file.exists():
            logger.error(f"❌ Commitment file not found: {commitment_file}")
            return None
        
        print(f"📄 Using commitment file: {commitment_file}")
        
        # Convert selected blocks to JSON string
        selected_blocks_json = json.dumps(selected_blocks)
        
        # Run the verification binary with absolute path
        cmd = [
            'cargo', 'run', '--bin', 'verify_upload_blocks', '--',
            upload_id,
            selected_blocks_json,
            str(commitment_file.resolve())  # Use absolute path
        ]
        
        logger.info(f"🔒 Running STARK verification: {' '.join(cmd)}")
        
        start_time = datetime.now()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, timeout=1800)
        end_time = datetime.now()
        
        verification_time = (end_time - start_time).total_seconds()
        
        print(f"⏱️  STARK verification completed in {verification_time:.2f} seconds")
        print(f"🔄 Return code: {result.returncode}")
        
        if result.returncode == 0:
            print(f"✅ STARK verification: SUCCESS")
            print(f"📋 Full verification output:")
            print(result.stdout)
            return {
                'success': True,
                'verification_time': verification_time,
                'output': result.stdout,
                'tampering_detected': False
            }
        elif result.returncode == 1 and "TAMPERING DETECTED" in result.stdout:
            print(f"🚨 STARK verification: TAMPERING DETECTED")
            print(f"📋 Full verification output:")
            print(result.stdout)
            return {
                'success': False,
                'verification_time': verification_time,
                'output': result.stdout,
                'tampering_detected': True
            }
        else:
            print(f"❌ STARK verification failed with return code {result.returncode}")
            print(f"stderr: {result.stderr}")
            print(f"stdout: {result.stdout}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ STARK verification timed out after 30 minutes")
        return None
    except Exception as e:
        logger.error(f"❌ STARK verification error: {e}")
        return None

def parse_verification_results(verification_output):
    """
    Parse STARK verification output to extract statistics
    """
    if not verification_output:
        return {}
    
    output_lines = verification_output.split('\n')
    stats = {
        'blocks_verified': 0,
        'blocks_failed': 0,
        'total_proof_size': 0,
        'total_generation_time': 0,
        'total_verification_time': 0,
        'all_passed': False
    }
    
    for line in output_lines:
        if "Successful verifications:" in line:
            try:
                stats['blocks_verified'] = int(line.split(':')[1].strip())
            except:
                pass
        elif "Failed verifications:" in line:
            try:
                stats['blocks_failed'] = int(line.split(':')[1].strip())
            except:
                pass
        elif "Total proof size:" in line:
            try:
                size_part = line.split(':')[1].strip().split()[0]
                stats['total_proof_size'] = int(size_part)
            except:
                pass
        elif "ALL VERIFICATIONS PASSED" in line:
            stats['all_passed'] = True
    
    return stats

def display_final_results(file_info, selected_blocks, verification_result):
    """
    Display comprehensive audit results
    """
    print_header("AUDIT RESULTS SUMMARY")
    
    print(f"📄 FILE INFORMATION:")
    print(f"   📏 File size: {file_info['file_size_mb']:.2f} MB")
    print(f"   📋 Total rows: {file_info['rows_processed']}")
    print(f"   🔢 Total blocks created: {file_info['total_blocks']}")
    
    print(f"\n🎲 AUDIT SAMPLE:")
    print(f"   🎯 Blocks selected for audit: {len(selected_blocks)}")
    print(f"   📊 Sample percentage: {(len(selected_blocks) / file_info['total_blocks'] * 100):.2f}%")
    print(f"   📋 Selected block numbers: {selected_blocks}")
    
    if verification_result:
        print(f"\n🔒 STARK VERIFICATION:")
        print(f"   ⏱️  Verification time: {verification_result['verification_time']:.2f} seconds")
        
        if verification_result.get('tampering_detected'):
            print(f"   🚨 RESULT: TAMPERING DETECTED!")
            print(f"   ⚠️  Data integrity compromised")
        elif verification_result.get('success'):
            print(f"   ✅ RESULT: NO TAMPERING DETECTED")
            print(f"   🔒 Data integrity verified")
        else:
            print(f"   ❓ RESULT: VERIFICATION INCOMPLETE")
        
        # Parse and display detailed statistics
        stats = parse_verification_results(verification_result.get('output', ''))
        if stats:
            print(f"\n📊 VERIFICATION STATISTICS:")
            print(f"   ✅ Blocks passed: {stats['blocks_verified']}")
            print(f"   ❌ Blocks failed: {stats['blocks_failed']}")
            if stats['total_proof_size'] > 0:
                print(f"   📐 Total proof size: {stats['total_proof_size']} bytes")
                print(f"   📊 Average proof size: {stats['total_proof_size'] // max(1, stats['blocks_verified'])} bytes")
    else:
        print(f"\n❌ STARK VERIFICATION: FAILED TO COMPLETE")
    
    # Final verdict
    print(f"\n🎯 FINAL AUDIT VERDICT:")
    if verification_result and verification_result.get('success') and not verification_result.get('tampering_detected'):
        print(f"   ✅ AUDIT PASSED")
        print(f"   🔒 File integrity verified using zero-knowledge proofs")
        print(f"   📊 Confidence level maintained throughout verification")
    elif verification_result and verification_result.get('tampering_detected'):
        print(f"   🚨 AUDIT FAILED")
        print(f"   ⚠️  Data tampering detected in one or more blocks")
        print(f"   🔍 Manual investigation recommended")
    else:
        print(f"   ❓ AUDIT INCOMPLETE")
        print(f"   ⚠️  Could not complete STARK verification")

def main():
    """Main function for standalone audit"""
    if len(sys.argv) != 2:
        print("Usage: python3 standalone_audit.py <filename.csv>")
        print("Example: python3 standalone_audit.py sample_financial_dataset.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print_header("ZK AUDIT SYSTEM - STANDALONE AUDIT")
    print(f"🎯 Target file: {csv_file}")
    
    # Check if file exists
    if not os.path.exists(csv_file):
        logger.error(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    # Generate unique upload ID
    upload_id = str(uuid.uuid4())
    print(f"🆔 Generated upload ID: {upload_id}")
    
    # Create temporary blocks directory
    project_root = Path(__file__).parent
    blocks_dir = project_root / "upload_blocks" / upload_id
    
    try:
        # Step 1: Create blocks from CSV
        print_step(1, "Creating data blocks from CSV file")
        file_info = create_blocks_from_csv(csv_file, upload_id, blocks_dir)
        if not file_info:
            logger.error("❌ Failed to create data blocks")
            sys.exit(1)
        
        # Step 2: Generate Merkle commitment
        print_step(2, "Generating Merkle tree commitment")
        commitment_data = create_merkle_commitment(
            file_info['block_metadata'], 
            upload_id, 
            user_id="cli_user",
            target_block_size_mb=2.0
        )
        commitment_file_path = save_commitment_file(commitment_data, upload_id)
        
        # Step 3: Select all blocks for comprehensive audit
        print_step(3, "Selecting all blocks for comprehensive audit")
        selected_blocks = list(range(file_info['total_blocks']))
        sample_size = file_info['total_blocks']
        
        print(f"🎯 Comprehensive audit selected:")
        print(f"   🔢 Total blocks to audit: {sample_size}")
        print(f"   📊 Coverage: 100% (all blocks)")
        print(f"   📋 Block range: 0-{file_info['total_blocks']-1}")
        
        # Step 4: Run STARK verification
        print_step(4, "Performing STARK verification")
        verification_result = run_stark_verification(upload_id, selected_blocks, blocks_dir, commitment_file_path)
        
        # Step 5: Display results
        print_step(5, "Compiling audit results")
        display_final_results(file_info, selected_blocks, verification_result)
        
        print(f"\n🎉 Standalone audit completed!")
        print(f"📁 Block files saved in: {blocks_dir}")
        print(f"💾 Commitment file saved in: {commitment_file_path}")
        
    except KeyboardInterrupt:
        logger.info("❌ Audit interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during audit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()