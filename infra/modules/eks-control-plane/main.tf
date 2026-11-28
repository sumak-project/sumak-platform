# Reviewed EKS versions are >=1.28 and receive default envelope encryption with
# an AWS-owned key; Learner Lab does not authorize custom IAM/KMS ownership.
# The cluster remains private through its private-only control-plane endpoint.
#trivy:ignore:AVD-AWS-0039
resource "aws_eks_cluster" "this" {
  name                      = var.name
  role_arn                  = var.cluster_role_arn
  version                   = var.cluster_version
  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  vpc_config {
    subnet_ids              = var.private_subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = false
  }

  tags = var.tags

  lifecycle {
    precondition {
      condition     = length(var.availability_zones) == length(var.private_subnet_ids)
      error_message = "Each private subnet must have one corresponding availability zone."
    }
  }
}
