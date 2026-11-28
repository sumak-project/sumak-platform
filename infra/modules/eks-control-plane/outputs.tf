output "cluster_arn" {
  description = "ARN of the EKS control plane."
  value       = aws_eks_cluster.this.arn
}

output "cluster_endpoint" {
  description = "Private endpoint of the EKS control plane."
  value       = aws_eks_cluster.this.endpoint
}

output "cluster_name" {
  description = "Name of the EKS control plane."
  value       = aws_eks_cluster.this.name
}
