// Lambda function: Block Fetcher
// Fetches selected blocks from S3 based on audit plan

use aws_config::BehaviorVersion;
use aws_sdk_s3 as s3;
use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use tracing::{info, error};
use zk_audit_lambda::{BlockFetcherEvent, BlockFetcherResponse, BlockData, LambdaError};

async fn function_handler(event: LambdaEvent<BlockFetcherEvent>) -> Result<BlockFetcherResponse, Error> {
    let (event, _context) = event.into_parts();
    
    info!("Processing block fetcher request for user: {}, upload: {}", 
          event.user_id, event.upload_id);
    
    // Initialize AWS S3 client
    let config = aws_config::load_defaults(BehaviorVersion::v2025_01_17()).await;
    let s3_client = s3::Client::new(&config);
    
    let mut blocks_fetched = Vec::new();
    let mut errors = Vec::new();
    
    // Generate audit ID for this request
    let audit_id = format!("audit_{}_{}", 
                          event.user_id, 
                          chrono::Utc::now().format("%Y%m%d_%H%M%S"));
    
    // Fetch each selected block
    for &block_index in &event.selected_blocks {
        let block_id = format!("block_{:04}", block_index + 1);
        let s3_key = format!("uploads/{}/blocks/{}/{}.csv", 
                            event.user_id, event.upload_id, block_id);
        
        info!("Fetching block: {} from {}", block_id, s3_key);
        
        match fetch_block_from_s3(&s3_client, &event.s3_bucket, &s3_key).await {
            Ok((content, size)) => {
                blocks_fetched.push(BlockData {
                    block_id,
                    block_index,
                    s3_key,
                    content: Some(content),
                    size_bytes: size,
                });
                info!("Successfully fetched block: block_{:04}", block_index + 1);
            }
            Err(e) => {
                error!("Failed to fetch block {}: {}", block_id, e);
                errors.push(format!("Block {}: {}", block_id, e));
            }
        }
    }
    
    let success = errors.is_empty();
    let error_message = if errors.is_empty() {
        None
    } else {
        Some(errors.join("; "))
    };
    
    info!("Block fetcher completed: {} blocks fetched, {} errors", 
          blocks_fetched.len(), errors.len());
    
    Ok(BlockFetcherResponse {
        audit_id,
        blocks_fetched,
        success,
        error_message,
    })
}

async fn fetch_block_from_s3(
    s3_client: &s3::Client,
    bucket: &str,
    key: &str,
) -> Result<(String, u64), LambdaError> {
    let response = s3_client
        .get_object()
        .bucket(bucket)
        .key(key)
        .send()
        .await
        .map_err(|e| LambdaError::S3Error(format!("Failed to fetch {}: {}", key, e)))?;
    
    let content_length = response.content_length().unwrap_or(0) as u64;
    
    let body = response
        .body
        .collect()
        .await
        .map_err(|e| LambdaError::S3Error(format!("Failed to read body: {}", e)))?;
    
    let content = String::from_utf8(body.to_vec())
        .map_err(|e| LambdaError::S3Error(format!("Invalid UTF-8 content: {}", e)))?;
    
    Ok((content, content_length))
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .with_target(false)
        .without_time()
        .init();

    info!("Starting Block Fetcher Lambda function");
    
    run(service_fn(function_handler)).await
}