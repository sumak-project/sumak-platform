output "endpoint" {
  description = "Private PostgreSQL endpoint."
  value       = aws_db_instance.this.address
}

output "port" {
  description = "PostgreSQL listener port."
  value       = aws_db_instance.this.port
}

output "security_group_id" {
  description = "Security group attached to the PostgreSQL instance."
  value       = aws_security_group.this.id
}

output "master_user_secret_arn" {
  description = "AWS-managed master credential secret."
  value       = aws_db_instance.this.master_user_secret[0].secret_arn
  sensitive   = true
}

output "owner_secret_arns" {
  description = "Credential placeholder secrets keyed by owner and role."
  value       = { for key, secret in aws_secretsmanager_secret.owner_credentials : key => secret.arn }
}
