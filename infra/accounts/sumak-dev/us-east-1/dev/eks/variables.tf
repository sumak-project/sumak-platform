variable "cluster_name" {
  description = "Name of the existing DEV EKS control plane provisioned outside this ticket."
  type        = string
}

variable "node_role_arn" {
  description = "ARN of the existing Learner Lab EKS node role."
  type        = string
}

variable "private_subnet_ids" {
  description = "Three existing DEV private application/EKS subnet IDs."
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) == 3 && length(distinct(var.private_subnet_ids)) == 3
    error_message = "private_subnet_ids must contain exactly three distinct private subnets."
  }
}

variable "availability_zones" {
  description = "Three distinct DEV availability zones corresponding to private_subnet_ids."
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) == 3 && length(distinct(var.availability_zones)) == 3
    error_message = "availability_zones must contain exactly three distinct zones."
  }
}

variable "root_volume_size" {
  description = "Encrypted gp2 node root volume size in GiB."
  type        = number
  default     = 50

  validation {
    condition     = var.root_volume_size >= 20 && var.root_volume_size <= 100
    error_message = "root_volume_size must be between 20 and 100 GiB."
  }
}
