variable "name" {
  description = "Name assigned to the private SSM bastion."
  type        = string
}

variable "subnet_id" {
  description = "Private application subnet in which the bastion is placed."
  type        = string
}

variable "vpc_id" {
  description = "VPC containing the bastion and SSM interface endpoints."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private application subnets used by the SSM interface endpoints."
  type        = set(string)
}

variable "vpc_cidr" {
  description = "VPC CIDR allowed to reach the private SSM interface endpoints."
  type        = string
}

variable "instance_profile_name" {
  description = "Pre-provisioned Learner Lab instance profile. This module never creates IAM resources."
  type        = string
  default     = "LabInstanceProfile"
}

variable "instance_type" {
  description = "Learner Lab-compatible EC2 type, constrained to at most the large class."
  type        = string
  default     = "t3.small"

  validation {
    condition     = can(regex("^[a-z0-9]+\\.(nano|micro|small|medium|large)$", var.instance_type))
    error_message = "The bastion instance type must be an EC2 nano, micro, small, medium, or large class."
  }
}

variable "root_volume_size_gib" {
  description = "Encrypted gp3 root volume size in GiB."
  type        = number
  default     = 20

  validation {
    condition     = var.root_volume_size_gib >= 8 && var.root_volume_size_gib <= 100
    error_message = "The root volume must be between 8 and 100 GiB."
  }
}

variable "existing_running_ec2_count" {
  description = "Observed running EC2 count before this bastion is added."
  type        = number

  validation {
    condition     = var.existing_running_ec2_count >= 0 && var.existing_running_ec2_count <= 8
    error_message = "At most eight other EC2 instances may be running before adding the bastion."
  }
}

variable "existing_running_vcpu_count" {
  description = "Observed running EC2 vCPU count in the region before this bastion is added."
  type        = number

  validation {
    condition     = var.existing_running_vcpu_count >= 0 && var.existing_running_vcpu_count <= 30
    error_message = "The existing running EC2 fleet must leave two vCPUs within the 32-vCPU boundary."
  }
}

variable "tags" {
  description = "Additional tags applied to bastion resources."
  type        = map(string)
  default     = {}
}
