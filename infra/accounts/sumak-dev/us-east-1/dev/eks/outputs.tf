output "cluster_arn" {
  description = "ARN of the DEV EKS control plane."
  value       = module.control_plane.cluster_arn
}

output "cluster_endpoint" {
  description = "Private endpoint of the DEV EKS control plane."
  value       = module.control_plane.cluster_endpoint
}

output "cluster_name" {
  description = "Name of the DEV EKS control plane."
  value       = module.control_plane.cluster_name
}

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

output "private_aws_api_interface_endpoint_ids" {
  description = "Required private AWS API interface endpoint IDs."
  value       = module.private_aws_api_connectivity.interface_endpoint_ids
}

output "s3_gateway_endpoint_id" {
  description = "S3 gateway endpoint ID used by private EKS nodes."
  value       = module.private_aws_api_connectivity.s3_endpoint_id
}
