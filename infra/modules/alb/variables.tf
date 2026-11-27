variable "name" {
  description = "Name of the application load balancer and target group."
  type        = string
}

variable "subnet_ids" {
  description = "Public subnet IDs spanning at least two availability zones."
  type        = list(string)

  validation {
    condition     = length(distinct(var.subnet_ids)) >= 2
    error_message = "subnet_ids must contain at least two distinct public subnets."
  }
}

variable "security_group_id" {
  description = "Existing ALB security group IDs; this bounded stack passes exactly one."
  type        = list(string)

  validation {
    condition     = length(var.security_group_id) == 1
    error_message = "security_group_id must contain exactly the existing ALB security group."
  }
}

variable "vpc_id" {
  description = "VPC containing the target group."
  type        = string
}

variable "listener_port" {
  description = "Public HTTPS listener port."
  type        = number
  default     = 443
}

variable "target_port" {
  description = "Logical gateway target port."
  type        = number
  default     = 8443
}

variable "target_protocol" {
  description = "Protocol used between the ALB and logical gateway."
  type        = string
  default     = "HTTPS"

  validation {
    condition     = contains(["HTTP", "HTTPS"], var.target_protocol)
    error_message = "target_protocol must be HTTP or HTTPS."
  }
}

variable "health_check_path" {
  description = "Technical health endpoint exposed by the logical gateway."
  type        = string
  default     = "/health/ready"
}

variable "health_check_interval" {
  description = "Seconds between target health checks."
  type        = number
  default     = 30
}

variable "deregistration_delay" {
  description = "Seconds allowed for connection draining."
  type        = number
  default     = 60
}

variable "idle_timeout" {
  description = "ALB idle timeout in seconds, including WSS connections."
  type        = number
  default     = 120
}

variable "enable_https_listener" {
  description = "Creates the HTTPS listener only after an authorized ACM certificate is available."
  type        = bool
  default     = false
}

variable "certificate_arn" {
  description = "Authorized ACM certificate ARN. Required when enable_https_listener is true."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition     = !var.enable_https_listener || (var.certificate_arn != null && can(regex("^arn:aws:acm:", var.certificate_arn)))
    error_message = "certificate_arn must be an ACM ARN when the HTTPS listener is enabled."
  }
}

variable "tags" {
  description = "Tags applied to the ALB and target group."
  type        = map(string)
  default     = {}
}
