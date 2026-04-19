variable "vpc_id" {
  description = "The ID of the VPC where Redis will be deployed"
  type        = string
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
}

variable "private_subnets" {
  description = "A list of subnet IDs for the Redis subnet group"
  type        = list(string)
}
