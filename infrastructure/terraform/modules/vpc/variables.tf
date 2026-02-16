variable "vpc_cidr" {}
variable "public_subnet_cidr" { type = list(string) }
variable "private_subnet_cidr" { type = list(string) }
variable "azs" { type = list(string) }
