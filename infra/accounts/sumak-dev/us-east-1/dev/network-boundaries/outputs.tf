output "security_group_ids" {
  description = "Plan-only DEV security group identifiers by tier and owner."
  value       = module.network_security_groups.security_group_ids
}

output "network_subnet_ids_by_tier" {
  description = "Existing DEV subnet identifiers consumed from the network stack."
  value       = data.terraform_remote_state.network.outputs.subnet_ids_by_tier
}
