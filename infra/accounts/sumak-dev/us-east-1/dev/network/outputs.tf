output "vpc_id" {
  description = "DEV VPC ID."
  value       = module.dev_vpc.vpc_id
}

output "subnet_ids_by_tier" {
  description = "DEV subnet IDs grouped by network tier and availability zone."
  value       = module.dev_vpc.subnet_ids_by_tier
}

output "availability_zone_ids" {
  description = "Physical availability zone IDs used by the DEV VPC."
  value       = module.dev_vpc.availability_zone_ids
}
