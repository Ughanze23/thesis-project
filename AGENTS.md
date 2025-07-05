# AGENTS.md - Coding Guidelines for IK Thesis Project

## Build/Test Commands
- **Run main script**: `python 0_generate_dataset/generate_blocks_commitments.py`
- **Test Python syntax**: `python -m py_compile 0_generate_dataset/generate_blocks_commitments.py`
- **Check dependencies**: `python -c "import pandas, hashlib, json, math, tqdm, datetime"`

## Code Style Guidelines
- **Language**: Python 3.12+
- **Imports**: Standard library first, then third-party (pandas, tqdm), group by type
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Docstrings**: Use triple quotes with brief description for all functions/classes
- **Type hints**: Not currently used but preferred for new code
- **Line length**: Keep reasonable (current code ~80-120 chars)
- **Error handling**: Use descriptive error messages, raise appropriate exceptions

## Project Structure
- `0_generate_dataset/`: Data processing and block generation scripts
- `1_blocks_commitments/`: Generated Merkle commitment outputs (JSON)
- Generated CSV blocks are gitignored

## Key Dependencies
- pandas: CSV data manipulation
- hashlib: SHA3-256 hashing
- tqdm: Progress bars
- Standard library: os, json, math, datetime

## Cryptographic Standards
- Hash algorithm: SHA3-256 only
- Merkle trees must have power-of-2 leaf count
- Authentication paths required for all blocks