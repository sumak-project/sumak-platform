output "vpc_id" {
  description = "ID of the environment VPC."
  value       = aws_vpc.this.id
}

output "subnet_ids_by_tier" {
  description = "Subnet IDs grouped by public, application, and data tier."
  value = {
    for tier in keys(local.subnet_tiers) :
    tier => {
      for key, subnet in aws_subnet.this :
      local.subnets[key].zone_name => subnet.id
      if local.subnets[key].tier == tier
    }
  }
}

output "availability_zone_ids" {
  description = "Physical availability zone IDs used by the layout."
  value       = { for name, zone in var.availability_zones : name => zone.zone_id }
}
