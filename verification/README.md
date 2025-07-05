# Merkle Commitment Verification

This directory contains tools to verify data integrity and test tampering detection with actual block files.

## 📁 Files

- `verify_blocks.py` - Verify blocks against Merkle commitment
- `simple_tamper_test.py` - Test tampering detection with real data
- `MANUAL_TAMPERING_STEPS.md` - Step-by-step tampering guide

## 🔍 Quick Test

```bash
# Test tampering detection with real block files
python3 simple_tamper_test.py
```

## 🧪 Manual Tampering

Follow the guide in `MANUAL_TAMPERING_STEPS.md` to manually modify block files and see how the system detects any changes.

## 🎯 What This Proves

The system cryptographically detects ANY modification to committed data, providing the foundation for trustworthy zero-knowledge proofs.