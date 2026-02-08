variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "db_username" {
  description = "Database username"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  default     = "dev"
}