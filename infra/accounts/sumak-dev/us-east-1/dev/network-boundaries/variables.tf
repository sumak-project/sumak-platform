variable "allowed_ingress_ipv4_cidrs" {
  description = "Reviewed IPv4 client origins allowed to reach the public ingress boundary."
  type        = set(string)
  default     = []
}

variable "allowed_ingress_ipv6_cidrs" {
  description = "Reviewed IPv6 client origins allowed to reach the public ingress boundary."
  type        = set(string)
  default     = []
}

variable "alb_listener_port" {
  description = "Reviewed TLS listener port for the public ingress boundary."
  type        = number
  default     = 443
}

variable "gateway_port" {
  description = "Reviewed TLS port from the ingress boundary to the logical gateway."
  type        = number
  default     = 8443
}

variable "bff_port" {
  description = "Reviewed TLS port from the logical gateway to each BFF."
  type        = number
  default     = 8443
}

variable "services" {
  description = "Reviewed service ownership and private gRPC/database paths. Empty until service deployment is authorized."
  type = map(object({
    grpc_port     = number
    allowed_bffs  = set(string)
    database_port = optional(number)
  }))
  default = {}
}

variable "brokers" {
  description = "Reviewed private broker listeners and their explicitly allowed service callers."
  type = map(object({
    tls_port         = number
    allowed_services = set(string)
  }))
  default = {}
}

variable "management_endpoints" {
  description = "Reviewed private management endpoints reachable only from the SSM bastion boundary."
  type = map(object({
    port = number
  }))
  default = {}
}
