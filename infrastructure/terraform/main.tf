module "vpc" {
  source = "./modules/vpc"

  vpc_cidr            = "10.0.0.0/16"
  public_subnet_cidr  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidr = ["10.0.3.0/24", "10.0.4.0/24"]
  azs                 = ["us-east-1a", "us-east-1b"]
}

module "eks" {
  source = "./modules/eks"

  cluster_name    = "event-monitoring-cluster"
  cluster_version = "1.28"
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  public_subnets  = module.vpc.public_subnets
}

module "rds" {
  source = "./modules/rds"

  db_name     = "eventdb"
  db_username = var.db_username
  db_password = var.db_password
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
}

module "redis" {
  source = "./modules/redis"

  subnet_ids        = module.vpc.private_subnets
  security_group_id = module.vpc.redis_sg_id
}

