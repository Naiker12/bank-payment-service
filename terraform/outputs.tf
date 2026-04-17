output "redis_host" {
  value = aws_elasticache_cluster.catalog.cache_nodes[0].address
}

output "start_payment_queue_url" {
  value = aws_sqs_queue.start_payment.url
}

output "check_balance_queue_url" {
  value = aws_sqs_queue.check_balance.url
}

output "transaction_queue_url" {
  value = aws_sqs_queue.transaction.url
}

output "payment_table_name" {
  value = aws_dynamodb_table.payment.name
}

output "catalog_bucket" {
  value = aws_s3_bucket.catalog.bucket
}
