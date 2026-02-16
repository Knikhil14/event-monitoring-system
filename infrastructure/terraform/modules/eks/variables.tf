variable "cluster_name" {}
variable "cluster_version" {
  default = "1.28"
}
variable "vpc_id" {}
variable "private_subnets" { type = list(string) }
variable "public_subnets" { type = list(string) }
