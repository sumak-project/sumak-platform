output "node_group_arn" {
  description = "ARN of the DEV managed node group."
  value       = module.managed_node_group.node_group_arn
}

output "node_group_name" {
  description = "Name of the DEV managed node group."
  value       = module.managed_node_group.node_group_name
}

output "launch_template_id" {
  description = "ID of the DEV node launch template."
  value       = module.managed_node_group.launch_template_id
}
