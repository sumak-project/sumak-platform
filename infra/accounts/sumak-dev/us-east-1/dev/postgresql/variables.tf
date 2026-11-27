variable "vpc_id" {
  description = "Existing DEV VPC ID."
  type        = string
}

variable "private_data_subnet_ids" {
  description = "Existing DEV private data subnet IDs."
  type        = list(string)
}

variable "identity_service_security_group_id" {
  description = "Existing identity service security group ID."
  type        = string
}

variable "config_service_security_group_id" {
  description = "Existing config service security group ID."
  type        = string
}
