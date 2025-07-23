#!/usr/bin/env python3
"""
Cloud-based ZK Data Integrity Audit System - Data Ingestion Pipeline
Extends the existing block generation to work with AWS S3 and DynamoDB.
"""

import os
import pandas as pd
import hashlib
import json
import math
import uuid
import boto3
from datetime import datetime
from tqdm import tqdm
from typing import List, Dict, Tuple, Optional
import tempfile
import shutil

class CloudMerkleTree:
    """Merkle Tree implementation optimized for cloud storage."""
    
    def __init__(self, leaves: List[str]):
        self.leaves = leaves
        self.tree = self._build_tree(leaves)
        self.root = self.tree[0] if self.tree else None
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
                right = current_level[i + 1]
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

class CloudDataIngestionPipeline:
    """Main pipeline for ingesting data into cloud-based ZK audit system."""
    
    def __init__(self, 
                 aws_region: str = 'us-east-1',
                 s3_bucket: Optional[str] = None,
                 dynamodb_table: Optional[str] = None,
                 user_id: Optional[str] = None):
        """Initialize cloud pipeline with AWS configuration."""
        self.aws_region = aws_region
        self.s3_bucket = s3_bucket or 'zk-audit-system-data'
        self.dynamodb_table = dynamodb_table or 'zk-audit-metadata'
        self.user_id = user_id or str(uuid.uuid4())
        
        # Initialize AWS clients
        try:
            self.s3_client = boto3.client('s3', region_name=aws_region)
            self.dynamodb = boto3.resource('dynamodb', region_name=aws_region)
            self.table = self.dynamodb.Table(self.dynamodb_table)
        except Exception as e:
            print(f"⚠️  Warning: AWS clients not initialized: {e}")
            print("📝 Running in local mode only")
            self.s3_client = None
            self.dynamodb = None
            self.table = None
    
    def compute_block_hash(self, data: bytes) -> str:
        """Compute SHA3-256 hash of block data."""
        hasher = hashlib.sha3_256()
        hasher.update(data)
        return hasher.hexdigest()
    
    def split_into_blocks(self, 
                         input_file: str, 
                         target_block_size_mb: float = 2.0) -> Tuple[List[Dict], int, str]:
        """Split CSV file into blocks and prepare for cloud upload."""
        print(f"📁 Processing file: {input_file}")
        
        # Get file info
        file_size = os.path.getsize(input_file)
        file_size_mb = file_size / (1024 * 1024)
        print(f"📊 File size: {file_size_mb:.2f} MB")
        
        # Calculate optimal block count (power of 2)
        estimated_blocks = math.ceil(file_size_mb / target_block_size_mb)
        power_of_2_blocks = 2 ** math.ceil(math.log2(estimated_blocks))
        target_block_size_bytes = int(target_block_size_mb * 1024 * 1024)
        
        print(f"🧮 Estimated blocks needed: {estimated_blocks}")
        print(f"🔢 Rounded to power of 2: {power_of_2_blocks}")
        print(f"📦 Target block size: {target_block_size_mb} MB")
        
        # Create temporary directory for block processing
        temp_dir = tempfile.mkdtemp(prefix='zk_audit_blocks_')
        upload_id = str(uuid.uuid4())
        
        try:
            # Read and process CSV data
            df = pd.read_csv(input_file)
            total_rows = len(df)
            print(f"📋 Total rows to process: {total_rows:,}")
            
            block_metadata = []
            current_row = 0
            
            # Generate blocks
            for block_index in tqdm(range(power_of_2_blocks), desc="Creating blocks"):
                block_id = f"block_{block_index + 1:04d}"
                block_file = os.path.join(temp_dir, f"{block_id}.csv")
                
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
                    block_hash = self.compute_block_hash(block_content)
                
                metadata = {
                    "block_id": block_id,
                    "hash": block_hash,
                    "row_count": len(block_data),
                    "size_bytes": len(block_content),
                    "size_mb": len(block_content) / (1024 * 1024),
                    "is_empty": len(block_data) == 0,
                    "timestamp": datetime.now().isoformat(),
                    "upload_id": upload_id,
                    "user_id": self.user_id,
                    "local_path": block_file
                }
                
                block_metadata.append(metadata)
            
            return block_metadata, power_of_2_blocks, upload_id
        
        finally:
            # Note: temp_dir cleanup handled by caller
            pass
    
    def create_merkle_commitment(self, block_metadata: List[Dict]) -> Dict:
        """Create Merkle tree commitment from block metadata."""
        print("\n🌳 Building Merkle tree commitment...")
        
        # Extract block hashes
        block_hashes = [block['hash'] for block in block_metadata]
        
        # Build Merkle tree
        merkle_tree = CloudMerkleTree(block_hashes)
        
        # Add authentication paths to metadata
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
            "root_hash": [merkle_tree.root],  # List format for compatibility
            "total_blocks": len(block_metadata),
            "data_blocks": len(non_empty_blocks),
            "empty_blocks": empty_blocks,
            "blocks_power_of_2": True,
            "timestamp": datetime.now().isoformat(),
            "upload_id": block_metadata[0]['upload_id'] if block_metadata else "",
            "user_id": self.user_id,
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
        
        return commitment_data
    
    def upload_to_s3(self, block_metadata: List[Dict], commitment_data: Dict) -> bool:
        """Upload blocks and commitment to S3."""
        if not self.s3_client:
            print("⚠️  S3 client not available, skipping upload")
            return False
        
        print("\n☁️  Uploading to S3...")
        upload_id = commitment_data['upload_id']
        
        try:
            # Upload blocks
            for block in tqdm(block_metadata, desc="Uploading blocks"):
                s3_key = f"uploads/{self.user_id}/blocks/{upload_id}/{block['block_id']}.csv"
                
                with open(block['local_path'], 'rb') as f:
                    self.s3_client.put_object(
                        Bucket=self.s3_bucket,
                        Key=s3_key,
                        Body=f,
                        Metadata={
                            'block_id': block['block_id'],
                            'hash': block['hash'],
                            'user_id': self.user_id,
                            'upload_id': upload_id
                        }
                    )
                
                # Update metadata with S3 location
                block['s3_bucket'] = self.s3_bucket
                block['s3_key'] = s3_key
            
            # Upload commitment
            commitment_key = f"uploads/{self.user_id}/commitments/{upload_id}/merkle_commitment.json"
            commitment_json = json.dumps(commitment_data, indent=2)
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=commitment_key,
                Body=commitment_json.encode(),
                ContentType='application/json',
                Metadata={
                    'user_id': self.user_id,
                    'upload_id': upload_id,
                    'total_blocks': str(commitment_data['total_blocks'])
                }
            )
            
            commitment_data['s3_bucket'] = self.s3_bucket
            commitment_data['s3_key'] = commitment_key
            
            print(f"✅ Uploaded {len(block_metadata)} blocks to S3")
            print(f"✅ Uploaded commitment to S3")
            
            return True
            
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")
            return False
    
    def store_metadata_dynamodb(self, commitment_data: Dict) -> bool:
        """Store metadata in DynamoDB for fast querying."""
        if not self.table:
            print("⚠️  DynamoDB client not available, skipping metadata storage")
            return False
        
        print("\n💾 Storing metadata in DynamoDB...")
        
        try:
            upload_id = commitment_data['upload_id']
            
            # Store main commitment record
            main_record = {
                'pk': f"USER#{self.user_id}",
                'sk': f"UPLOAD#{upload_id}",
                'entity_type': 'commitment',
                'upload_id': upload_id,
                'user_id': self.user_id,
                'root_hash': commitment_data['root_hash'][0],
                'total_blocks': commitment_data['total_blocks'],
                'data_blocks': commitment_data['data_blocks'],
                'timestamp': commitment_data['timestamp'],
                's3_bucket': commitment_data.get('s3_bucket'),
                's3_key': commitment_data.get('s3_key'),
                'merkle_tree_height': commitment_data['merkle_tree_structure']['height'],
                'size_statistics': commitment_data['size_statistics']
            }
            
            self.table.put_item(Item=main_record)
            
            # Store individual block metadata for fast access
            for i, block in enumerate(commitment_data['block_metadata']):
                block_record = {
                    'pk': f"UPLOAD#{upload_id}",
                    'sk': f"BLOCK#{i:04d}",
                    'entity_type': 'block',
                    'block_id': block['block_id'],
                    'block_index': i,
                    'hash': block['hash'],
                    'authentication_path': block['authentication_path'],
                    'size_mb': block['size_mb'],
                    'is_empty': block['is_empty'],
                    's3_bucket': block.get('s3_bucket'),
                    's3_key': block.get('s3_key'),
                    'upload_id': upload_id,
                    'user_id': self.user_id
                }
                
                self.table.put_item(Item=block_record)
            
            print(f"✅ Stored metadata for {len(commitment_data['block_metadata'])} blocks")
            return True
            
        except Exception as e:
            print(f"❌ DynamoDB storage failed: {e}")
            return False
    
    def process_file(self, 
                    input_file: str, 
                    target_block_size_mb: float = 2.0,
                    upload_to_cloud: bool = True) -> Dict:
        """Complete pipeline to process a file for ZK audit system."""
        print(f"🚀 Starting cloud data ingestion pipeline")
        print(f"👤 User ID: {self.user_id}")
        
        temp_dir = None
        try:
            # Step 1: Split into blocks
            block_metadata, total_blocks, upload_id = self.split_into_blocks(
                input_file, target_block_size_mb
            )
            temp_dir = os.path.dirname(block_metadata[0]['local_path']) if block_metadata else None
            
            # Step 2: Create Merkle commitment
            commitment_data = self.create_merkle_commitment(block_metadata)
            
            if upload_to_cloud:
                # Step 3: Upload to S3
                s3_success = self.upload_to_s3(block_metadata, commitment_data)
                
                # Step 4: Store metadata in DynamoDB
                dynamo_success = self.store_metadata_dynamodb(commitment_data)
                
                # Update success status
                commitment_data['cloud_upload_success'] = s3_success and dynamo_success
            else:
                commitment_data['cloud_upload_success'] = True  # Local mode
            
            # Step 5: Save local copy
            output_file = f"commitment_{upload_id}.json"
            with open(output_file, 'w') as f:
                json.dump(commitment_data, f, indent=2)
            
            # Summary
            print(f"\n{'='*60}")
            print("📋 INGESTION COMPLETE")
            print(f"{'='*60}")
            print(f"🆔 Upload ID: {upload_id}")
            print(f"📦 Total blocks: {total_blocks}")
            print(f"📊 Data blocks: {commitment_data['data_blocks']}")
            print(f"🌳 Merkle root: {commitment_data['root_hash'][0]}")
            print(f"☁️  Cloud upload: {'✅' if commitment_data.get('cloud_upload_success') else '❌'}")
            print(f"💾 Local copy: {output_file}")
            
            return commitment_data
            
        finally:
            # Cleanup temporary files
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Interactive main function for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZK Audit System - Data Ingestion Pipeline')
    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('--block-size', type=float, default=2.0, 
                       help='Target block size in MB (default: 2.0)')
    parser.add_argument('--user-id', help='User ID (default: random UUID)')
    parser.add_argument('--local-only', action='store_true', 
                       help='Skip cloud upload (local processing only)')
    parser.add_argument('--s3-bucket', help='S3 bucket name')
    parser.add_argument('--dynamodb-table', help='DynamoDB table name')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"❌ Error: Input file '{args.input_file}' not found")
        return 1
    
    # Initialize pipeline
    pipeline = CloudDataIngestionPipeline(
        user_id=args.user_id,
        s3_bucket=args.s3_bucket,
        dynamodb_table=args.dynamodb_table
    )
    
    # Process file
    try:
        result = pipeline.process_file(
            args.input_file,
            args.block_size,
            upload_to_cloud=not args.local_only
        )
        
        if result.get('cloud_upload_success', False):
            print(f"\n🎉 Success! Ready for ZK audit system")
            return 0
        else:
            print(f"\n⚠️  Completed with warnings (check cloud configuration)")
            return 0
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())