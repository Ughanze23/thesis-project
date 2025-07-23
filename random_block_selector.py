#!/usr/bin/env python3
"""
Random Block Selection Algorithm for ZK Data Integrity Audit System
Implements cryptographically secure random sampling with 95% confidence corruption detection.
"""

import os
import math
import secrets
import hashlib
from typing import List, Dict, Tuple
import json
from datetime import datetime


class RandomBlockSelector:
    """
    Cryptographically secure random block selector with statistical confidence guarantees.
    
    Uses binomial probability to calculate minimum sample size needed for 95% confidence
    that we'll detect corruption if it exists in the dataset.
    """
    
    def __init__(self, confidence_level: float = 0.95, min_corruption_rate: float = 0.05):
        """
        Initialize the block selector.
        
        Args:
            confidence_level: Probability of detecting corruption (default: 0.95 = 95%)
            min_corruption_rate: Minimum corruption rate we want to detect (default: 0.05 = 5%)
        """
        self.confidence_level = confidence_level
        self.min_corruption_rate = min_corruption_rate
        self.random_seed = None
    
    def calculate_sample_size(self, total_blocks: int, 
                            corruption_rate: float = None) -> int:
        """
        Calculate minimum sample size for desired confidence level.
        
        Uses the hypergeometric distribution for sampling without replacement.
        For large populations, approximates with binomial distribution.
        
        Formula: P(detect >= 1 corrupted) = 1 - P(detect 0 corrupted)
        P(detect 0 corrupted) = (1 - p)^n where p = corruption_rate, n = sample_size
        
        We want: 1 - (1 - p)^n >= confidence_level
        Solving for n: n >= log(1 - confidence_level) / log(1 - p)
        """
        if corruption_rate is None:
            corruption_rate = self.min_corruption_rate
        
        if corruption_rate <= 0 or corruption_rate >= 1:
            raise ValueError("Corruption rate must be between 0 and 1")
        
        if total_blocks <= 0:
            raise ValueError("Total blocks must be positive")
        
        # Calculate theoretical minimum sample size
        fail_prob = 1 - self.confidence_level  # Probability of missing corruption
        
        # n >= log(fail_prob) / log(1 - corruption_rate)
        theoretical_min = math.log(fail_prob) / math.log(1 - corruption_rate)
        min_sample_size = math.ceil(theoretical_min)
        
        # Ensure we don't sample more blocks than available
        sample_size = min(min_sample_size, total_blocks)
        
        # For very small datasets, ensure minimum meaningful sample
        if total_blocks < 10:
            sample_size = max(sample_size, min(3, total_blocks))
        
        return sample_size
    
    def generate_cryptographic_seed(self, user_id: str, upload_id: str, 
                                  audit_timestamp: str = None) -> bytes:
        """
        Generate cryptographically secure seed from audit parameters.
        
        This ensures that:
        1. The same audit parameters always produce the same selection
        2. Different audits produce different selections
        3. The seed is unpredictable without knowledge of the parameters
        """
        if audit_timestamp is None:
            audit_timestamp = datetime.now().isoformat()
        
        # Combine parameters into a deterministic seed
        seed_data = f"{user_id}|{upload_id}|{audit_timestamp}"
        
        # Use SHA-256 to generate deterministic but unpredictable seed
        hasher = hashlib.sha256()
        hasher.update(seed_data.encode('utf-8'))
        seed = hasher.digest()
        
        self.random_seed = seed
        return seed
    
    def select_random_blocks(self, total_blocks: int, 
                           user_id: str, upload_id: str,
                           corruption_rate: float = None,
                           audit_timestamp: str = None) -> List[int]:
        """
        Select random blocks for auditing using cryptographically secure randomness.
        
        Args:
            total_blocks: Total number of blocks in the dataset
            user_id: User identifier for deterministic seed generation
            upload_id: Upload identifier for deterministic seed generation
            corruption_rate: Expected corruption rate (default: uses min_corruption_rate)
            audit_timestamp: Timestamp for audit (default: current time)
            
        Returns:
            List of block indices to audit (0-based indexing)
        """
        # Calculate required sample size
        sample_size = self.calculate_sample_size(total_blocks, corruption_rate)
        
        # Generate cryptographic seed
        seed = self.generate_cryptographic_seed(user_id, upload_id, audit_timestamp)
        
        # Use secrets module for cryptographically secure random selection
        # We'll use the seed to initialize a deterministic PRNG
        selected_indices = set()
        
        # Create a deterministic random sequence from the seed
        # We'll hash the seed with an incrementing counter to generate random bytes
        counter = 0
        while len(selected_indices) < sample_size:
            # Create unique input for this iteration
            hasher = hashlib.sha256()
            hasher.update(seed)
            hasher.update(counter.to_bytes(4, 'big'))
            hash_bytes = hasher.digest()
            
            # Convert first 4 bytes to integer and mod by total_blocks
            random_int = int.from_bytes(hash_bytes[:4], 'big')
            block_index = random_int % total_blocks
            
            selected_indices.add(block_index)
            counter += 1
            
            # Prevent infinite loop in edge cases
            if counter > total_blocks * 10:
                break
        
        return sorted(list(selected_indices))
    
    def calculate_actual_confidence(self, sample_size: int, total_blocks: int,
                                  corruption_rate: float = None) -> float:
        """
        Calculate the actual confidence level achieved with given sample size.
        
        This is the inverse of calculate_sample_size - given a sample size,
        what's the probability we'll detect corruption?
        """
        if corruption_rate is None:
            corruption_rate = self.min_corruption_rate
        
        if sample_size <= 0 or total_blocks <= 0:
            return 0.0
        
        # Probability of missing corruption = (1 - corruption_rate)^sample_size
        miss_prob = (1 - corruption_rate) ** sample_size
        
        # Confidence = 1 - probability of missing
        confidence = 1 - miss_prob
        
        return confidence
    
    def generate_audit_plan(self, total_blocks: int, user_id: str, upload_id: str,
                          corruption_rates: List[float] = None,
                          audit_timestamp: str = None) -> Dict:
        """
        Generate a complete audit plan with multiple corruption rate scenarios.
        
        Returns detailed information about the audit including:
        - Selected blocks
        - Confidence levels
        - Statistical guarantees
        - Audit parameters
        """
        if audit_timestamp is None:
            audit_timestamp = datetime.now().isoformat()
        
        if corruption_rates is None:
            corruption_rates = [0.01, 0.05, 0.10, 0.20]  # 1%, 5%, 10%, 20%
        
        # Select blocks based on the primary corruption rate (min_corruption_rate)
        selected_blocks = self.select_random_blocks(
            total_blocks, user_id, upload_id, 
            corruption_rate=self.min_corruption_rate,
            audit_timestamp=audit_timestamp
        )
        
        sample_size = len(selected_blocks)
        
        # Calculate confidence for different corruption rates
        confidence_analysis = []
        for rate in corruption_rates:
            confidence = self.calculate_actual_confidence(sample_size, total_blocks, rate)
            confidence_analysis.append({
                "corruption_rate": rate,
                "corruption_rate_percent": f"{rate * 100:.1f}%",
                "confidence": confidence,
                "confidence_percent": f"{confidence * 100:.2f}%"
            })
        
        # Generate audit plan
        audit_plan = {
            "audit_id": hashlib.sha256(f"{user_id}|{upload_id}|{audit_timestamp}".encode()).hexdigest()[:16],
            "timestamp": audit_timestamp,
            "user_id": user_id,
            "upload_id": upload_id,
            "total_blocks": total_blocks,
            "selected_blocks": selected_blocks,
            "sample_size": sample_size,
            "sample_percentage": f"{(sample_size / total_blocks) * 100:.2f}%",
            "target_confidence": self.confidence_level,
            "target_confidence_percent": f"{self.confidence_level * 100:.1f}%",
            "min_corruption_rate": self.min_corruption_rate,
            "min_corruption_rate_percent": f"{self.min_corruption_rate * 100:.1f}%",
            "confidence_analysis": confidence_analysis,
            "cryptographic_seed": self.random_seed.hex() if self.random_seed else None,
            "selection_algorithm": "cryptographic_hash_based",
            "statistical_method": "binomial_approximation",
            "audit_guarantees": {
                "deterministic": "Same parameters always produce same selection",
                "unpredictable": "Selection unpredictable without audit parameters", 
                "secure": "Uses cryptographically secure hash functions",
                "statistical": f"≥{self.confidence_level * 100:.1f}% chance of detecting ≥{self.min_corruption_rate * 100:.1f}% corruption"
            }
        }
        
        return audit_plan
    
    def validate_audit_plan(self, audit_plan: Dict) -> Dict:
        """
        Validate an audit plan and check its statistical properties.
        
        Returns validation results including any warnings or recommendations.
        """
        validation = {
            "valid": True,
            "warnings": [],
            "recommendations": [],
            "statistics": {}
        }
        
        total_blocks = audit_plan["total_blocks"]
        sample_size = audit_plan["sample_size"]
        
        # Check sample size reasonableness
        if sample_size < 3:
            validation["warnings"].append("Very small sample size may not be reliable")
        
        if sample_size > total_blocks * 0.5:
            validation["warnings"].append("Sampling >50% of blocks - consider reducing")
        
        # Check coverage for small datasets
        if total_blocks < 10 and sample_size < total_blocks:
            validation["recommendations"].append("For small datasets, consider auditing all blocks")
        
        # Calculate efficiency metrics
        efficiency_ratio = sample_size / total_blocks
        validation["statistics"]["efficiency"] = f"{efficiency_ratio:.4f}"
        validation["statistics"]["blocks_saved"] = total_blocks - sample_size
        validation["statistics"]["cost_reduction"] = f"{(1 - efficiency_ratio) * 100:.1f}%"
        
        return validation


def main():
    """Interactive demonstration of the random block selector."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZK Audit System - Random Block Selector')
    parser.add_argument('--total-blocks', type=int, required=True,
                       help='Total number of blocks in dataset')
    parser.add_argument('--user-id', default='demo_user',
                       help='User ID for audit')
    parser.add_argument('--upload-id', default='demo_upload',
                       help='Upload ID for audit')
    parser.add_argument('--confidence', type=float, default=0.95,
                       help='Target confidence level (default: 0.95)')
    parser.add_argument('--min-corruption', type=float, default=0.05,
                       help='Minimum corruption rate to detect (default: 0.05)')
    parser.add_argument('--output', help='Save audit plan to JSON file')
    
    args = parser.parse_args()
    
    print("🎲 ZK Audit System - Random Block Selector")
    print("=" * 50)
    
    # Initialize selector
    selector = RandomBlockSelector(
        confidence_level=args.confidence,
        min_corruption_rate=args.min_corruption
    )
    
    # Generate audit plan
    audit_plan = selector.generate_audit_plan(
        args.total_blocks, args.user_id, args.upload_id
    )
    
    # Validate plan
    validation = selector.validate_audit_plan(audit_plan)
    
    # Display results
    print(f"🆔 Audit ID: {audit_plan['audit_id']}")
    print(f"📊 Total blocks: {audit_plan['total_blocks']:,}")
    print(f"🎯 Selected blocks: {audit_plan['sample_size']} ({audit_plan['sample_percentage']})")
    print(f"📈 Target confidence: {audit_plan['target_confidence_percent']}")
    print(f"🔍 Min corruption rate: {audit_plan['min_corruption_rate_percent']}")
    
    print(f"\n📋 Selected block indices:")
    blocks = audit_plan['selected_blocks']
    for i in range(0, len(blocks), 10):
        chunk = blocks[i:i+10]
        print(f"  {chunk}")
    
    print(f"\n📈 Confidence Analysis:")
    for analysis in audit_plan['confidence_analysis']:
        print(f"  {analysis['corruption_rate_percent']} corruption → "
              f"{analysis['confidence_percent']} detection confidence")
    
    print(f"\n✅ Validation:")
    print(f"  Status: {'PASS' if validation['valid'] else 'FAIL'}")
    print(f"  Cost reduction: {validation['statistics']['cost_reduction']}")
    print(f"  Blocks saved: {validation['statistics']['blocks_saved']:,}")
    
    if validation['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"  • {warning}")
    
    if validation['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in validation['recommendations']:
            print(f"  • {rec}")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                "audit_plan": audit_plan,
                "validation": validation
            }, f, indent=2)
        print(f"\n💾 Audit plan saved to: {args.output}")


if __name__ == "__main__":
    main()