output "repository_arn" {
  description = "DEV identity service ECR repository ARN."
  value       = module.identity_ecr.repository_arn
}

output "repository_url" {
  description = "DEV identity service ECR repository URL."
  value       = module.identity_ecr.repository_url
}
