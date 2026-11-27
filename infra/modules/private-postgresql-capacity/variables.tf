variable "name" {
  description = "Name of the private PostgreSQL instance."
  type        = string
}

variable "vpc_id" {
  description = "VPC that contains the private data subnets."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private data subnet IDs in distinct availability zones."
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "At least two private data subnets are required."
  }
}

variable "owner_security_group_ids" {
  description = "Service security groups allowed to reach PostgreSQL."
  type = object({
    identity = string
    config   = string
  })
}

variable "instance_class" {
  description = "Learner Lab-compatible RDS instance class."
  type        = string
  default     = "db.t3.medium"

  validation {
    condition     = contains(["db.t3.micro", "db.t3.small", "db.t3.medium"], var.instance_class)
    error_message = "The instance class must not exceed a db.t3.medium."
  }
}

variable "allocated_storage" {
  description = "Allocated gp2 storage in GiB."
  type        = number
  default     = 20

  validation {
    condition     = var.allocated_storage >= 20 && var.allocated_storage <= 100
    error_message = "Allocated storage must be between 20 and 100 GiB."
  }
}

variable "engine_version" {
  description = "PostgreSQL engine version approved for this environment."
  type        = string
  default     = "16.6"
}

variable "tags" {
  description = "Additional resource tags."
  type        = map(string)
  default     = {}
}
