#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { ZkAuditSystemStack } from '../lib/zk-audit-system-stack';

const app = new cdk.App();

// Get environment configuration
const account = process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID;
const region = process.env.CDK_DEFAULT_REGION || process.env.AWS_DEFAULT_REGION || 'us-east-1';

if (!account) {
    console.error('❌ AWS account ID not found. Please set CDK_DEFAULT_ACCOUNT or AWS_ACCOUNT_ID');
    process.exit(1);
}

console.log(`🚀 Deploying ZK Audit System to account ${account} in region ${region}`);

new ZkAuditSystemStack(app, 'ZkAuditSystemStack', {
    env: {
        account,
        region,
    },
    description: 'Zero-Knowledge Data Integrity Audit System - Cloud Infrastructure',
    tags: {
        Project: 'ZK-Audit-System',
        Environment: process.env.ENVIRONMENT || 'dev',
        Owner: process.env.OWNER || 'zk-audit-team',
    },
});