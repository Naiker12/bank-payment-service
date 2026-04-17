provider "aws" {
  region = var.aws_region
}

# ── DynamoDB ──────────────────────────────────────────────────────────────────

resource "aws_dynamodb_table" "payment" {
  name         = "payment"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "traceId"

  attribute {
    name = "traceId"
    type = "S"
  }

  tags = { Name = "payment-table" }
}

# ── S3 ────────────────────────────────────────────────────────────────────────

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "catalog" {
  bucket = "digital-bank-catalog-${random_id.suffix.hex}"
}

# ── Redis (ElastiCache) ───────────────────────────────────────────────────────

resource "aws_security_group" "lambda" {
  name   = "payment-lambda-sg"
  vpc_id = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "redis" {
  name   = "redis-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "redis-subnet-group"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_cluster" "catalog" {
  cluster_id           = "catalog-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]
}

# ── SQS ──────────────────────────────────────────────────────────────────────

resource "aws_sqs_queue" "start_payment" {
  name                       = "start-payment-queue"
  visibility_timeout_seconds = 60
}

resource "aws_sqs_queue" "check_balance" {
  name                       = "check-balance-queue"
  visibility_timeout_seconds = 60
}

resource "aws_sqs_queue" "transaction" {
  name                       = "transaction-queue"
  visibility_timeout_seconds = 60
}
