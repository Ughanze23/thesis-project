// Lambda function: Hash Generator
// Computes SHA3 hashes for fetched blocks

use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use tracing::{info, error, warn};
use zk_audit_lambda::{
    HashGeneratorEvent, HashGeneratorResponse, BlockHashData, 
    compute_sha3_hash_str, LambdaError
};

async fn function_handler(event: LambdaEvent<HashGeneratorEvent>) -> Result<HashGeneratorResponse, Error> {
    let (event, _context) = event.into_parts();
    
    info!("Processing hash generation request for audit: {}", event.audit_id);
    info!("Number of blocks to hash: {}", event.blocks.len());
    
    let mut block_hashes = Vec::new();
    let mut errors = Vec::new();
    
    // Process each block
    for block in &event.blocks {
        info!("Hashing block: {}", block.block_id);
        
        match generate_block_hash(block).await {
            Ok(hash_data) => {
                block_hashes.push(hash_data);
                info!("Successfully hashed block: {}", block.block_id);
            }
            Err(e) => {
                error!("Failed to hash block {}: {}", block.block_id, e);
                errors.push(format!("Block {}: {}", block.block_id, e));
            }
        }
    }
    
    let success = errors.is_empty();
    let error_message = if errors.is_empty() {
        None
    } else {
        Some(errors.join("; "))
    };
    
    info!("Hash generation completed: {} hashes generated, {} errors", 
          block_hashes.len(), errors.len());
    
    Ok(HashGeneratorResponse {
        audit_id: event.audit_id,
        block_hashes,
        success,
        error_message,
    })
}

async fn generate_block_hash(block: &zk_audit_lambda::BlockData) -> Result<BlockHashData, LambdaError> {
    // Get block content
    let content = block.content.as_ref()
        .ok_or_else(|| LambdaError::InvalidInput("Block content is empty".to_string()))?;
    
    // Compute SHA3 hash of content
    let hash = compute_sha3_hash_str(content);
    
    // For this implementation, we need to fetch the authentication path from DynamoDB
    // Since this is a simplified version, we'll use placeholder authentication paths
    // In a production system, this would query DynamoDB for the pre-computed paths
    let authentication_path = fetch_authentication_path(&block.block_id, block.block_index).await?;
    
    Ok(BlockHashData {
        block_id: block.block_id.clone(),
        block_index: block.block_index,
        hash,
        authentication_path,
        size_bytes: block.size_bytes,
    })
}

async fn fetch_authentication_path(block_id: &str, block_index: u32) -> Result<Vec<String>, LambdaError> {
    // TODO: In production, this would fetch from DynamoDB
    // For now, we'll use a placeholder implementation
    
    info!("Fetching authentication path for block: {} (index: {})", block_id, block_index);
    
    // This is a simplified placeholder - in reality, we'd query DynamoDB
    // based on the upload_id to get the pre-computed Merkle tree authentication paths
    let placeholder_path = vec![
        "placeholder_sibling_hash_1".to_string(),
        "placeholder_sibling_hash_2".to_string(),
    ];
    
    Ok(placeholder_path)
}

// In a production system, this would be implemented to fetch from DynamoDB
async fn _fetch_authentication_path_from_dynamodb(
    _block_id: &str, 
    _block_index: u32,
    _upload_id: &str
) -> Result<Vec<String>, LambdaError> {
    // Initialize DynamoDB client
    let config = aws_config::load_defaults(aws_config::BehaviorVersion::v2024_03_28()).await;
    let dynamodb = aws_sdk_dynamodb::Client::new(&config);
    
    // Query for block metadata
    let table_name = std::env::var("DYNAMODB_TABLE")
        .unwrap_or_else(|_| "zk-audit-metadata".to_string());
    
    let result = dynamodb
        .get_item()
        .table_name(table_name)
        .key("pk", aws_sdk_dynamodb::types::AttributeValue::S(format!("UPLOAD#{}", _upload_id)))
        .key("sk", aws_sdk_dynamodb::types::AttributeValue::S(format!("BLOCK#{:04}", _block_index)))
        .send()
        .await
        .map_err(|e| LambdaError::DynamoDbError(e.to_string()))?;
    
    if let Some(item) = result.item {
        if let Some(auth_path_attr) = item.get("authentication_path") {
            if let aws_sdk_dynamodb::types::AttributeValue::Ss(path_strings) = auth_path_attr {
                return Ok(path_strings.clone());
            }
        }
    }
    
    Err(LambdaError::DynamoDbError("Authentication path not found".to_string()))
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .with_target(false)
        .without_time()
        .init();

    info!("Starting Hash Generator Lambda function");
    
    run(service_fn(function_handler)).await
}