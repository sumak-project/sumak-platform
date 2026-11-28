variable "cluster_role_arn" {
  description = "ARN of the pre-provisioned Learner Lab EKS cluster role."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::632080579751:role/(.*/)?[^/]*LabEksClusterRole[^/]*$", var.cluster_role_arn))
    error_message = "cluster_role_arn must reference the pre-provisioned Learner Lab EKS cluster role in the assigned DEV account."
  }
}

variable "cluster_version" {
  description = "Reviewed Kubernetes minor version for the DEV EKS control plane."
  type        = string
  default     = "1.36"

  validation {
    condition     = contains(["1.32", "1.33", "1.34", "1.35", "1.36", "1.37"], var.cluster_version)
    error_message = "cluster_version must be one of the reviewed EKS minor versions."
  }
}

variable "node_role_arn" {
  description = "ARN of the existing Learner Lab EKS node role."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::632080579751:role/(.*/)?[^/]*LabEksNodeRole[^/]*$", var.node_role_arn))
    error_message = "node_role_arn must reference the pre-provisioned Learner Lab EKS node role in the assigned DEV account."
  }
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
