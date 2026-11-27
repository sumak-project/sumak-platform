variable "name" {
  description = "Name of the managed node group and its launch template."
  type        = string
}

variable "cluster_name" {
  description = "Name of the existing EKS cluster."
  type        = string
}

variable "node_role_arn" {
  description = "ARN of the pre-provisioned Learner Lab EKS node role."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:role/", var.node_role_arn))
    error_message = "node_role_arn must be an IAM role ARN supplied by Learner Lab."
  }
}

variable "subnet_ids" {
  description = "Exactly three existing private subnet IDs, one per availability zone."
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) == 3 && length(distinct(var.subnet_ids)) == 3
    error_message = "subnet_ids must contain exactly three distinct private subnets."
  }
}

variable "availability_zones" {
  description = "Exactly three distinct availability zones corresponding to subnet_ids."
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) == 3 && length(distinct(var.availability_zones)) == 3
    error_message = "availability_zones must contain exactly three distinct zones."
  }
}

variable "root_volume_size" {
  description = "Encrypted gp2 root volume size in GiB; Learner Lab permits at most 100 GiB."
  type        = number
  default     = 50

  validation {
    condition     = var.root_volume_size >= 20 && var.root_volume_size <= 100
    error_message = "root_volume_size must be between 20 and 100 GiB."
  }
}

variable "tags" {
  description = "Tags applied to node-group resources."
  type        = map(string)
  default     = {}
}
