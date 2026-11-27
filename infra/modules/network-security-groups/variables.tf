variable "name_prefix" {
  description = "Environment-specific prefix applied to every managed security group."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.name_prefix))
    error_message = "name_prefix must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "vpc_id" {
  description = "VPC that owns the security groups."
  type        = string

  validation {
    condition     = can(regex("^vpc-[0-9a-f]+$", var.vpc_id))
    error_message = "vpc_id must be an AWS VPC identifier."
  }
}

variable "allowed_ingress_ipv4_cidrs" {
  description = "Reviewed IPv4 origins allowed to reach the public ALB TLS listener."
  type        = set(string)
  default     = []

  validation {
    condition = alltrue([
      for cidr in var.allowed_ingress_ipv4_cidrs :
      can(cidrnetmask(cidr))
    ])
    error_message = "Every allowed ingress IPv4 value must be a valid CIDR."
  }
}

variable "allowed_ingress_ipv6_cidrs" {
  description = "Reviewed IPv6 origins allowed to reach the public ALB TLS listener."
  type        = set(string)
  default     = []
}

variable "alb_listener_port" {
  description = "Reviewed TLS listener port exposed by the ALB."
  type        = number

  validation {
    condition     = var.alb_listener_port >= 1 && var.alb_listener_port <= 65535 && var.alb_listener_port != 22
    error_message = "alb_listener_port must be between 1 and 65535 and must not expose the SSH port."
  }
}

variable "gateway_port" {
  description = "Reviewed TLS port used from the ALB to the logical API gateway."
  type        = number

  validation {
    condition     = var.gateway_port >= 1 && var.gateway_port <= 65535
    error_message = "gateway_port must be between 1 and 65535."
  }
}

variable "bff_port" {
  description = "Reviewed TLS port used from the logical gateway to each BFF."
  type        = number

  validation {
    condition     = var.bff_port >= 1 && var.bff_port <= 65535
    error_message = "bff_port must be between 1 and 65535."
  }
}

variable "services" {
  description = "Application services, their reviewed gRPC ports, allowed BFF callers, and optional owned PostgreSQL ports."
  type = map(object({
    grpc_port     = number
    allowed_bffs  = set(string)
    database_port = optional(number)
  }))

  validation {
    condition = alltrue(flatten([
      for service in values(var.services) : [
        service.grpc_port >= 1 && service.grpc_port <= 65535,
        alltrue([for bff in service.allowed_bffs : contains(["mobile", "admin"], bff)]),
        try(service.database_port >= 1 && service.database_port <= 65535, true),
      ]
    ]))
    error_message = "Service ports must be between 1 and 65535, and allowed_bffs may contain only mobile or admin."
  }
}

variable "brokers" {
  description = "Owned broker listeners and the application services allowed to reach each listener."
  type = map(object({
    tls_port         = number
    allowed_services = set(string)
  }))
  default = {}

  validation {
    condition = alltrue(flatten([
      for broker in values(var.brokers) : [
        broker.tls_port >= 1 && broker.tls_port <= 65535,
        alltrue([for service in broker.allowed_services : contains(keys(var.services), service)]),
      ]
    ]))
    error_message = "Broker ports must be between 1 and 65535, and every allowed service must exist in services."
  }
}

variable "management_endpoints" {
  description = "Private administrative endpoints reachable only from the SSM bastion."
  type = map(object({
    port = number
  }))
  default = {}

  validation {
    condition = alltrue([
      for endpoint in values(var.management_endpoints) :
      endpoint.port >= 1 && endpoint.port <= 65535
    ])
    error_message = "Management endpoint ports must be between 1 and 65535."
  }
}

variable "tags" {
  description = "Tags applied to every managed security group."
  type        = map(string)
  default     = {}
}
