output "state_bucket_arn" {
  description = "ARN of the same-account DEV Terraform state bucket."
  value       = module.state_backend.arn
}

output "state_bucket_name" {
  description = "Name of the same-account DEV Terraform state bucket."
  value       = module.state_backend.bucket
}
