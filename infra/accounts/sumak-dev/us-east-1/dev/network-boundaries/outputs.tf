output "security_group_ids" {
  description = "Plan-only DEV security group identifiers by tier and owner."
  value       = module.network_security_groups.security_group_ids
}

output "alb_security_group_id" {
  description = "Existing DEV ALB security group identifier."
  value       = module.network_security_groups.security_group_ids["alb"]
}

output "network_subnet_ids_by_tier" {
  description = "Existing DEV subnet identifiers consumed from the network stack."
  value       = data.terraform_remote_state.network.outputs.subnet_ids_by_tier
}

output "network_vpc_id" {
  description = "Existing DEV VPC identifier consumed from the network stack."
  value       = data.terraform_remote_state.network.outputs.vpc_id
}
