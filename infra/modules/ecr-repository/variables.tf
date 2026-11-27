variable "repository_name" {
  description = "Private ECR repository name managed in one account and environment."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]+(?:[._/-][a-z0-9]+)*$", var.repository_name))
    error_message = "repository_name must be a valid lowercase ECR repository name."
  }
}

variable "retained_image_count" {
  description = "Maximum number of images retained in the repository."
  type        = number
  default     = 30

  validation {
    condition     = var.retained_image_count >= 1
    error_message = "retained_image_count must be at least 1."
  }
}

variable "tags" {
  description = "Tags applied to every ECR repository."
  type        = map(string)
  default     = {}
}
