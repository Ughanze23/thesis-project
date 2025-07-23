#!/usr/bin/env python3
"""
CloudWatch Metrics Collection for ZK Audit System
Tracks performance, costs, and security metrics across the audit pipeline.
"""

import boto3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class AuditMetrics:
    """Data structure for audit performance metrics."""
    audit_id: str
    user_id: str
    upload_id: str
    total_blocks: int
    blocks_audited: int
    confidence_level: float
    
    # Timing metrics
    total_duration_ms: int
    block_fetch_time_ms: int
    hash_generation_time_ms: int
    stark_proof_time_ms: int
    verification_time_ms: int
    
    # Resource utilization
    lambda_duration_ms: Dict[str, int]
    lambda_memory_used_mb: Dict[str, int]
    s3_requests: int
    dynamodb_requests: int
    
    # Business metrics
    tampering_detected: bool
    verification_success_rate: float
    cost_estimate_usd: float


class ZKAuditMetricsCollector:
    """Collects and publishes metrics to CloudWatch."""
    
    def __init__(self, region: str = 'us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.namespace = 'ZKAudit/System'
    
    def publish_audit_metrics(self, metrics: AuditMetrics) -> None:
        """Publish comprehensive audit metrics to CloudWatch."""
        
        timestamp = datetime.utcnow()
        
        # Performance metrics
        performance_metrics = [
            {
                'MetricName': 'AuditDuration',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': metrics.user_id},
                    {'Name': 'UploadId', 'Value': metrics.upload_id}
                ],
                'Value': metrics.total_duration_ms,
                'Unit': 'Milliseconds',
                'Timestamp': timestamp
            },
            {
                'MetricName': 'BlocksAudited',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': metrics.user_id},
                    {'Name': 'ConfidenceLevel', 'Value': str(metrics.confidence_level)}
                ],
                'Value': metrics.blocks_audited,
                'Unit': 'Count',
                'Timestamp': timestamp
            },
            {
                'MetricName': 'VerificationSuccessRate',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': metrics.user_id}
                ],
                'Value': metrics.verification_success_rate * 100,
                'Unit': 'Percent',
                'Timestamp': timestamp
            },
            {
                'MetricName': 'TamperingDetected',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': metrics.user_id}
                ],
                'Value': 1 if metrics.tampering_detected else 0,
                'Unit': 'Count',
                'Timestamp': timestamp
            }
        ]
        
        # Lambda function performance
        for function_name, duration in metrics.lambda_duration_ms.items():
            performance_metrics.extend([
                {
                    'MetricName': 'LambdaDuration',
                    'Dimensions': [
                        {'Name': 'FunctionName', 'Value': function_name},
                        {'Name': 'UserId', 'Value': metrics.user_id}
                    ],
                    'Value': duration,
                    'Unit': 'Milliseconds',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'LambdaMemoryUsed',
                    'Dimensions': [
                        {'Name': 'FunctionName', 'Value': function_name},
                        {'Name': 'UserId', 'Value': metrics.user_id}
                    ],
                    'Value': metrics.lambda_memory_used_mb.get(function_name, 0),
                    'Unit': 'Megabytes',
                    'Timestamp': timestamp
                }
            ])
        
        # Cost metrics
        cost_metrics = [
            {
                'MetricName': 'EstimatedCost',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': metrics.user_id},
                    {'Name': 'Service', 'Value': 'Total'}
                ],
                'Value': metrics.cost_estimate_usd,
                'Unit': 'None',  # USD
                'Timestamp': timestamp
            }
        ]
        
        # Publish all metrics in batches (CloudWatch limit is 20 per request)
        all_metrics = performance_metrics + cost_metrics
        
        for i in range(0, len(all_metrics), 20):
            batch = all_metrics[i:i+20]
            try:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
                print(f"✅ Published {len(batch)} metrics to CloudWatch")
            except Exception as e:
                print(f"❌ Failed to publish metrics: {e}")
    
    def create_custom_dashboard(self) -> str:
        """Create a CloudWatch dashboard for ZK audit system monitoring."""
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "AuditDuration", "UserId", "ALL"],
                            [self.namespace, "BlocksAudited", "UserId", "ALL"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Audit Performance",
                        "yAxis": {
                            "left": {
                                "min": 0
                            }
                        }
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "VerificationSuccessRate", "UserId", "ALL"],
                            [self.namespace, "TamperingDetected", "UserId", "ALL"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Security Metrics",
                        "yAxis": {
                            "left": {
                                "min": 0,
                                "max": 100
                            }
                        }
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 6,
                    "width": 24,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "LambdaDuration", "FunctionName", "zk-audit-block-fetcher"],
                            [self.namespace, "LambdaDuration", "FunctionName", "zk-audit-hash-generator"],
                            [self.namespace, "LambdaDuration", "FunctionName", "zk-audit-stark-prover"],
                            [self.namespace, "LambdaDuration", "FunctionName", "zk-audit-stark-verifier"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Lambda Function Performance",
                        "yAxis": {
                            "left": {
                                "min": 0
                            }
                        }
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 12,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "EstimatedCost", "Service", "Total"]
                        ],
                        "period": 3600,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Cost Analysis",
                        "yAxis": {
                            "left": {
                                "min": 0
                            }
                        }
                    }
                }
            ]
        }
        
        dashboard_name = "ZK-Audit-System-Dashboard"
        
        try:
            response = self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            print(f"✅ Created CloudWatch dashboard: {dashboard_name}")
            return f"https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name={dashboard_name}"
        except Exception as e:
            print(f"❌ Failed to create dashboard: {e}")
            return ""
    
    def setup_alarms(self) -> List[str]:
        """Set up CloudWatch alarms for critical metrics."""
        
        alarms = [
            {
                'AlarmName': 'ZK-Audit-High-Duration',
                'MetricName': 'AuditDuration',
                'Threshold': 300000,  # 5 minutes in ms
                'ComparisonOperator': 'GreaterThanThreshold',
                'AlarmDescription': 'Audit taking longer than 5 minutes'
            },
            {
                'AlarmName': 'ZK-Audit-Tampering-Detected',
                'MetricName': 'TamperingDetected',
                'Threshold': 1,
                'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
                'AlarmDescription': 'Data tampering detected in audit'
            },
            {
                'AlarmName': 'ZK-Audit-Low-Success-Rate',
                'MetricName': 'VerificationSuccessRate',
                'Threshold': 90,  # 90%
                'ComparisonOperator': 'LessThanThreshold',
                'AlarmDescription': 'Verification success rate below 90%'
            },
            {
                'AlarmName': 'ZK-Audit-High-Cost',
                'MetricName': 'EstimatedCost',
                'Threshold': 10.0,  # $10 per audit
                'ComparisonOperator': 'GreaterThanThreshold',
                'AlarmDescription': 'Audit cost exceeds $10'
            }
        ]
        
        created_alarms = []
        
        for alarm_config in alarms:
            try:
                self.cloudwatch.put_metric_alarm(
                    AlarmName=alarm_config['AlarmName'],
                    ComparisonOperator=alarm_config['ComparisonOperator'],
                    EvaluationPeriods=2,
                    MetricName=alarm_config['MetricName'],
                    Namespace=self.namespace,
                    Period=300,
                    Statistic='Average',
                    Threshold=alarm_config['Threshold'],
                    ActionsEnabled=True,
                    AlarmDescription=alarm_config['AlarmDescription'],
                    Unit='None'
                )
                created_alarms.append(alarm_config['AlarmName'])
                print(f"✅ Created alarm: {alarm_config['AlarmName']}")
            except Exception as e:
                print(f"❌ Failed to create alarm {alarm_config['AlarmName']}: {e}")
        
        return created_alarms
    
    def get_audit_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get audit system analytics for the past N days."""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        metrics_to_query = [
            ('AuditDuration', 'Average'),
            ('BlocksAudited', 'Sum'),
            ('TamperingDetected', 'Sum'),
            ('VerificationSuccessRate', 'Average'),
            ('EstimatedCost', 'Sum')
        ]
        
        analytics = {}
        
        for metric_name, statistic in metrics_to_query:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace=self.namespace,
                    MetricName=metric_name,
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour
                    Statistics=[statistic]
                )
                
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    values = [dp[statistic] for dp in datapoints]
                    analytics[metric_name] = {
                        'current_value': values[-1] if values else 0,
                        'average': sum(values) / len(values) if values else 0,
                        'trend': 'up' if len(values) > 1 and values[-1] > values[0] else 'down',
                        'datapoints': len(values)
                    }
                else:
                    analytics[metric_name] = {
                        'current_value': 0,
                        'average': 0,
                        'trend': 'stable',
                        'datapoints': 0
                    }
                    
            except Exception as e:
                print(f"❌ Failed to get analytics for {metric_name}: {e}")
                analytics[metric_name] = {'error': str(e)}
        
        return analytics


def main():
    """Demo script for metrics collection."""
    
    print("📊 ZK Audit System - Metrics Collection Demo")
    print("=" * 50)
    
    # Initialize metrics collector
    collector = ZKAuditMetricsCollector()
    
    # Create sample audit metrics
    sample_metrics = AuditMetrics(
        audit_id="demo_audit_123",
        user_id="demo_user",
        upload_id="demo_upload_456",
        total_blocks=16,
        blocks_audited=4,
        confidence_level=95.0,
        total_duration_ms=45000,
        block_fetch_time_ms=5000,
        hash_generation_time_ms=8000,
        stark_proof_time_ms=25000,
        verification_time_ms=7000,
        lambda_duration_ms={
            'zk-audit-block-fetcher': 5000,
            'zk-audit-hash-generator': 8000,
            'zk-audit-stark-prover': 25000,
            'zk-audit-stark-verifier': 7000
        },
        lambda_memory_used_mb={
            'zk-audit-block-fetcher': 512,
            'zk-audit-hash-generator': 512,
            'zk-audit-stark-prover': 1024,
            'zk-audit-stark-verifier': 512
        },
        s3_requests=8,
        dynamodb_requests=12,
        tampering_detected=False,
        verification_success_rate=1.0,
        cost_estimate_usd=0.75
    )
    
    # Publish metrics
    print("\n📤 Publishing audit metrics...")
    collector.publish_audit_metrics(sample_metrics)
    
    # Create dashboard
    print("\n📊 Creating CloudWatch dashboard...")
    dashboard_url = collector.create_custom_dashboard()
    if dashboard_url:
        print(f"🌐 Dashboard URL: {dashboard_url}")
    
    # Setup alarms
    print("\n🚨 Setting up CloudWatch alarms...")
    alarms = collector.setup_alarms()
    print(f"✅ Created {len(alarms)} alarms")
    
    # Get analytics
    print("\n📈 Getting audit analytics...")
    analytics = collector.get_audit_analytics(days=7)
    
    print(f"\n{'='*50}")
    print("📋 ANALYTICS SUMMARY (Last 7 Days)")
    print(f"{'='*50}")
    
    for metric_name, data in analytics.items():
        if 'error' not in data:
            print(f"{metric_name}:")
            print(f"  Current: {data['current_value']:.2f}")
            print(f"  Average: {data['average']:.2f}")
            print(f"  Trend: {data['trend']}")
            print(f"  Data points: {data['datapoints']}")
            print()
    
    print("🎉 Metrics collection demo completed!")


if __name__ == "__main__":
    main()