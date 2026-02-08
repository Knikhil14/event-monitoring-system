terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  backend "s3" {
    bucket = "devops-project-tfstate"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  vpc_cidr           = "10.0.0.0/16"
  public_subnet_cidr = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidr = ["10.0.3.0/24", "10.0.4.0/24"]
  azs               = ["us-east-1a", "us-east-1b"]
}

# EKS Cluster Module
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = "event-monitoring-cluster"
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  public_subnets  = module.vpc.public_subnets
  
  node_groups = {
    general = {
      desired_size = 2
      max_size     = 3
      min_size     = 1
      instance_types = ["t3.medium"]
    }
  }
}

# RDS PostgreSQL Module
module "rds" {
  source = "./modules/rds"
  
  db_name     = "eventdb"
  db_username = var.db_username
  db_password = var.db_password
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
}

# Elasticache Redis Module
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "event-redis"
  engine              = "redis"
  node_type           = "cache.t3.micro"
  num_cache_nodes     = 1
  parameter_group_name = "default.redis7"
  port                = 6379
  security_group_ids  = [module.vpc.redis_sg_id]
  subnet_group_name   = aws_elasticache_subnet_group.redis.name
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "redis-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

# S3 for Logs
resource "aws_s3_bucket" "logs" {
  bucket = "event-monitoring-logs-${random_id.bucket_suffix.hex}"
}

resource "random_id" "bucket_suffix" {
  byte_length = 8
}