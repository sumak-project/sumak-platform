variable "name" {
  description = "Environment-specific name for the VPC."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.name))
    error_message = "name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "vpc_cidr" {
  description = "Non-overlapping IPv4 CIDR assigned to this environment."
  type        = string

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "vpc_cidr must be a valid IPv4 CIDR."
  }
}

variable "availability_zones" {
  description = "Exactly three physical AZ IDs and their public, application, and data subnet CIDRs."
  type = map(object({
    zone_id          = string
    public_cidr      = string
    application_cidr = string
    data_cidr        = string
  }))

  validation {
    condition = length(var.availability_zones) == 3 && alltrue([
      for zone in values(var.availability_zones) :
      can(regex("^[a-z0-9]+-az[0-9]+$", zone.zone_id)) &&
      can(cidrnetmask(zone.public_cidr)) &&
      can(cidrnetmask(zone.application_cidr)) &&
      can(cidrnetmask(zone.data_cidr))
    ])
    error_message = "availability_zones must define exactly three physical AZ IDs with valid tier CIDRs."
  }

  validation {
    condition = length(distinct(flatten([
      for zone in values(var.availability_zones) : [
        zone.public_cidr,
        zone.application_cidr,
        zone.data_cidr,
      ]
    ]))) == 9
    error_message = "All nine subnet CIDRs must be unique."
  }
}

variable "tags" {
  description = "Tags applied to every managed network resource."
  type        = map(string)
  default     = {}
}
