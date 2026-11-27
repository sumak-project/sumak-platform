provider "aws" {
  region              = "us-east-1"
  profile             = "sumak-dev"
  allowed_account_ids = ["632080579751"]

  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "Terraform"
      Project     = "SUMAK"
      Stack       = "eks-managed-node-group"
    }
  }
}

module "managed_node_group" {
  source = "../../../../../modules/eks-managed-node-group"

  name               = "sumak-dev-general"
  cluster_name       = var.cluster_name
  node_role_arn      = var.node_role_arn
  subnet_ids         = var.private_subnet_ids
  availability_zones = var.availability_zones
  root_volume_size   = var.root_volume_size

  tags = {
    Environment = "dev"
    Project     = "SUMAK"
    Tier        = "application"
  }
}
