variable "bucket_name" {
  description = "Globally unique name of the same-account Terraform state bucket."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "bucket_name must be a valid lowercase S3 bucket name."
  }
}

variable "tags" {
  description = "Tags applied to the Terraform state bucket."
  type        = map(string)
  default     = {}
}
