output "node_group_arn" {
  description = "ARN of the managed node group."
  value       = aws_eks_node_group.this.arn
}

output "node_group_name" {
  description = "Name of the managed node group."
  value       = aws_eks_node_group.this.node_group_name
}

output "launch_template_id" {
  description = "ID of the bounded node launch template."
  value       = aws_launch_template.nodes.id
}
