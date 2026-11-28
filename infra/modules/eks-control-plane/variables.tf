variable "name" {
  description = "Name of the EKS cluster."
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$", var.name))
    error_message = "name must be a valid EKS cluster name with at most 100 characters."
  }
}

variable "cluster_role_arn" {
  description = "ARN of the pre-provisioned Learner Lab EKS cluster role."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:role/(.*/)?[^/]*LabEksClusterRole[^/]*$", var.cluster_role_arn))
    error_message = "cluster_role_arn must reference a pre-provisioned Learner Lab EKS cluster role."
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

variable "private_subnet_ids" {
  description = "Exactly three existing private application subnet IDs."
  type        = list(string)

  validation {
    condition = (
      length(var.private_subnet_ids) == 3 &&
      length(distinct(var.private_subnet_ids)) == 3 &&
      alltrue([for subnet_id in var.private_subnet_ids : can(regex("^subnet-[0-9a-f]+$", subnet_id))])
    )
    error_message = "private_subnet_ids must contain exactly three distinct subnet IDs."
  }
}

variable "availability_zones" {
  description = "Three distinct availability zones corresponding to private_subnet_ids."
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) == 3 && length(distinct(var.availability_zones)) == 3
    error_message = "availability_zones must contain exactly three distinct zones."
  }
}

variable "tags" {
  description = "Tags applied to the EKS control plane."
  type        = map(string)
  default     = {}
}
