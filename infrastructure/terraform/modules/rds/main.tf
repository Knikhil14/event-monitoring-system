resource "aws_db_subnet_group" "this" {
  name       = "event-db-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_db_instance" "this" {
  identifier         = "event-db"
  engine             = "postgres"
  instance_class     = "db.t3.micro"
  allocated_storage  = 20
  username           = var.db_username
  password           = var.db_password
  db_subnet_group_name = aws_db_subnet_group.this.name
  skip_final_snapshot = true
}
