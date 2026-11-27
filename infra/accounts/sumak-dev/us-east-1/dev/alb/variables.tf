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
  description = "Logical gateway target protocol."
  type        = string
  default     = "HTTPS"
}

variable "health_check_path" {
  description = "Logical gateway readiness path."
  type        = string
  default     = "/actuator/health/readiness"
}

variable "health_check_interval" {
  description = "Seconds between target health checks."
  type        = number
  default     = 30
}

variable "deregistration_delay" {
  description = "Connection-draining period in seconds."
  type        = number
  default     = 60
}

variable "idle_timeout" {
  description = "Idle timeout compatible with reviewed WSS behavior."
  type        = number
  default     = 120
}

variable "enable_https_listener" {
  description = "Must remain false until SCRUM-35 certificate prerequisites are authorized."
  type        = bool
  default     = false
}

variable "certificate_arn" {
  description = "Authorized DEV ACM certificate ARN."
  type        = string
  default     = null
  nullable    = true
}
