resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr
  tags = {
    Name = "event-vpc"
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidr)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidr)
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidr[count.index]
  availability_zone = var.azs[count.index]
}

resource "aws_security_group" "redis" {
  name   = "redis-sg"
  vpc_id = aws_vpc.this.id
}
