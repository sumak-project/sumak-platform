output "repository_arn" {
  description = "ARN of the ECR repository."
  value       = aws_ecr_repository.this.arn
}

output "repository_url" {
  description = "Registry URL of the ECR repository."
  value       = aws_ecr_repository.this.repository_url
}
