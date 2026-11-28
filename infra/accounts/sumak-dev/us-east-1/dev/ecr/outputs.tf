output "repository_arn" {
  description = "DEV identity service ECR repository ARN."
  value       = module.identity_ecr.repository_arn
}

output "repository_url" {
  description = "DEV identity service ECR repository URL."
  value       = module.identity_ecr.repository_url
}

output "config_repository_arn" {
  description = "DEV configuration service ECR repository ARN."
  value       = module.config_ecr.repository_arn
}

output "config_repository_url" {
  description = "DEV configuration service ECR repository URL."
  value       = module.config_ecr.repository_url
}
