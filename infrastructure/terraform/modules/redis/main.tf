resource "aws_elasticache_subnet_group" "this" {
  name       = "redis-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_elasticache_cluster" "this" {
  cluster_id           = "event-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  subnet_group_name    = aws_elasticache_subnet_group.this.name
  security_group_ids   = [var.security_group_id]
}
