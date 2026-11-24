output "arn" {
  description = "ARN of the Terraform state bucket."
  value       = awscc_s3_bucket.this.arn
}

output "bucket" {
  description = "Name of the Terraform state bucket."
  value       = awscc_s3_bucket.this.bucket_name
}
