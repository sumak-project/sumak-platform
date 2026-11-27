variable "existing_running_ec2_count" {
  description = "Observed DEV account running EC2 count immediately before plan/apply."
  type        = number
}

variable "existing_running_vcpu_count" {
  description = "Observed us-east-1 running EC2 vCPU count immediately before plan/apply."
  type        = number
}
