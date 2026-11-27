variable "name" {
  description = "Name prefix for private AWS API connectivity resources."
  type        = string
}

variable "vpc_id" {
  description = "VPC that contains the private EKS subnets."
  type        = string
}

variable "vpc_cidr_block" {
  description = "IPv4 CIDR allowed to reach the interface endpoints over HTTPS."
  type        = string
}

variable "subnet_ids" {
  description = "Private subnet IDs where interface endpoints are created."
  type        = list(string)
}

variable "route_table_ids" {
  description = "Private route table IDs associated with the S3 gateway endpoint."
  type        = list(string)
}

variable "tags" {
  description = "Additional tags for private connectivity resources."
  type        = map(string)
  default     = {}
}
