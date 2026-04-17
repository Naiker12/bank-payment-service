locals {
  redis_host = aws_elasticache_cluster.catalog.cache_nodes[0].address
  redis_port = "6379"
}

# ── catalog_update ────────────────────────────────────────────────────────────

resource "aws_lambda_function" "catalog_update" {
  function_name    = "catalog-update"
  role             = var.lambda_role_arn
  runtime          = "python3.11"
  handler          = "catalog_update.handler"
  filename         = data.archive_file.payment_service_zip.output_path
  source_code_hash = data.archive_file.payment_service_zip.output_base64sha256
  timeout          = 30

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      REDIS_HOST     = local.redis_host
      REDIS_PORT     = local.redis_port
      CATALOG_BUCKET = aws_s3_bucket.catalog.bucket
    }
  }
}

# ── get_catalog ───────────────────────────────────────────────────────────────

resource "aws_lambda_function" "get_catalog" {
  function_name    = "get-catalog"
  role             = var.lambda_role_arn
  runtime          = "python3.11"
  handler          = "get_catalog.handler"
  filename         = data.archive_file.payment_service_zip.output_path
  source_code_hash = data.archive_file.payment_service_zip.output_base64sha256
  timeout          = 10

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      REDIS_HOST = local.redis_host
      REDIS_PORT = local.redis_port
    }
  }
}

# ── payment_initiator ────────────────────────────────────────────────────────

resource "aws_lambda_function" "payment_initiator" {
  function_name    = "payment-initiator"
  role             = var.lambda_role_arn
  runtime          = "python3.11"
  handler          = "payment_initiator.handler"
  filename         = data.archive_file.payment_service_zip.output_path
  source_code_hash = data.archive_file.payment_service_zip.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      CARD_API_URL            = var.card_api_url
      START_PAYMENT_QUEUE_URL = aws_sqs_queue.start_payment.url
      PAYMENT_TABLE           = aws_dynamodb_table.payment.name
    }
  }
}

# ── start_payment (SQS trigger) ──────────────────────────────────────────────

resource "aws_lambda_function" "start_payment" {
  function_name    = "start-payment"
  role             = var.lambda_role_arn
  runtime          = "python3.11"
  handler          = "start_payment.handler"
  filename         = data.archive_file.payment_service_zip.output_path
  source_code_hash = data.archive_file.payment_service_zip.output_base64sha256
  timeout          = 60

  environment {
    variables = {
      CHECK_BALANCE_QUEUE_URL = aws_sqs_queue.check_balance.url
      PAYMENT_TABLE           = aws_dynamodb_table.payment.name
    }
  }
}

resource "aws_lambda_event_source_mapping" "start_payment" {
  event_source_arn = aws_sqs_queue.start_payment.arn
  function_name    = aws_lambda_function.start_payment.arn
  batch_size       = 1
}

# ── check_balance (SQS trigger) ──────────────────────────────────────────────

resource "aws_lambda_function" "check_balance" {
  function_name    = "check-balance"
  role             = var.lambda_role_arn
  runtime          = "python3.11"
  handler          = "check_balance.handler"
  filename         = data.archive_file.payment_service_zip.output_path
  source_code_hash = data.archive_file.payment_service_zip.output_base64sha256
  timeout          = 60

  environment {
    variables = {
      TRANSACTION_QUEUE_URL = aws_sqs_queue.transaction.url
      CARD_API_URL          = var.card_api_url
      PAYMENT_TABLE         = aws_dynamodb_table.payment.name
    }
  }
}

resource "aws_lambda_event_source_mapping" "check_balance" {
  event_source_arn = aws_sqs_queue.check_balance.arn
  function_name    = aws_lambda_function.check_balance.arn
  batch_size       = 1
}

# ── transaction (SQS trigger) ────────────────────────────────────────────────

resource "aws_lambda_function" "transaction" {
  function_name    = "transaction"
  role             = var.lambda_role_arn
  runtime          = "python3.11"
  handler          = "transaction.handler"
  filename         = data.archive_file.payment_service_zip.output_path
  source_code_hash = data.archive_file.payment_service_zip.output_base64sha256
  timeout          = 60

  environment {
    variables = {
      CARD_API_URL  = var.card_api_url
      PAYMENT_TABLE = aws_dynamodb_table.payment.name
    }
  }
}

resource "aws_lambda_event_source_mapping" "transaction" {
  event_source_arn = aws_sqs_queue.transaction.arn
  function_name    = aws_lambda_function.transaction.arn
  batch_size       = 1
}

# ── get_payment_status ────────────────────────────────────────────────────────

resource "aws_lambda_function" "get_payment_status" {
  function_name    = "get-payment-status"
  role             = var.lambda_role_arn
  runtime          = "python3.11"
  handler          = "get_payment_status.handler"
  filename         = data.archive_file.payment_service_zip.output_path
  source_code_hash = data.archive_file.payment_service_zip.output_base64sha256
  timeout          = 10

  environment {
    variables = {
      PAYMENT_TABLE = aws_dynamodb_table.payment.name
    }
  }
}

# ── API Gateway Integrations ─────────────────────────────────────────────────

resource "aws_apigatewayv2_integration" "catalog_update" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.catalog_update.invoke_arn
}

resource "aws_apigatewayv2_route" "catalog_update_route" {
  api_id    = var.api_gateway_id
  route_key = "POST /catalog/update"
  target    = "integrations/${aws_apigatewayv2_integration.catalog_update.id}"
}

resource "aws_apigatewayv2_integration" "get_catalog" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_catalog.invoke_arn
}

resource "aws_apigatewayv2_route" "get_catalog_route" {
  api_id    = var.api_gateway_id
  route_key = "GET /catalog"
  target    = "integrations/${aws_apigatewayv2_integration.get_catalog.id}"
}

resource "aws_apigatewayv2_integration" "payment_initiator" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.payment_initiator.invoke_arn
}

resource "aws_apigatewayv2_route" "payment_route" {
  api_id    = var.api_gateway_id
  route_key = "POST /payment"
  target    = "integrations/${aws_apigatewayv2_integration.payment_initiator.id}"
}

resource "aws_apigatewayv2_integration" "get_payment_status" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_payment_status.invoke_arn
}

resource "aws_apigatewayv2_route" "get_payment_status_route" {
  api_id    = var.api_gateway_id
  route_key = "GET /payment/status/{traceId}"
  target    = "integrations/${aws_apigatewayv2_integration.get_payment_status.id}"
}

# ── Lambda Permissions (API Gateway) ─────────────────────────────────────────

resource "aws_lambda_permission" "api_gw_catalog_update" {
  statement_id  = "AllowExecutionFromAPIGatewayCatalogUpdate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.catalog_update.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_get_catalog" {
  statement_id  = "AllowExecutionFromAPIGatewayGetCatalog"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_catalog.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_payment" {
  statement_id  = "AllowExecutionFromAPIGatewayPayment"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.payment_initiator.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_payment_status" {
  statement_id  = "AllowExecutionFromAPIGatewayPaymentStatus"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_payment_status.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}
