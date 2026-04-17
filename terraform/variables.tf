variable "aws_region" {
  description = "Region de AWS"
  type        = string
  default     = "us-east-1"
}

variable "card_api_url" {
  description = "URL del API Gateway del bank-card-transaction-service"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN del rol IAM compartido para las Lambdas"
  type        = string
}

variable "api_gateway_id" {
  description = "ID del API Gateway compartido"
  type        = string
}

variable "api_gateway_execution_arn" {
  description = "Execution ARN del API Gateway compartido"
  type        = string
}

variable "private_subnet_ids" {
  description = "Subnets privadas donde viven las Lambdas y Redis"
  type        = list(string)
  default     = []
}

variable "vpc_id" {
  description = "VPC donde se despliega todo"
  type        = string
  default     = ""
}
