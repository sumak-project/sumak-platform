output "endpoint" {
  description = "Private PostgreSQL endpoint."
  value       = module.private_postgresql.endpoint
}

output "port" {
  description = "PostgreSQL listener port."
  value       = module.private_postgresql.port
}

output "owner_secret_arns" {
  description = "Credential placeholder secrets for the two database owners."
  value       = module.private_postgresql.owner_secret_arns
}
