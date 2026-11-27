provider "aws" {
  region              = "us-east-1"
  profile             = "sumak-dev"
  allowed_account_ids = ["632080579751"]

  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "Terraform"
      Project     = "SUMAK"
      Stack       = "eks"
    }
  }
}

data "aws_subnet" "private" {
  for_each = toset(var.private_subnet_ids)
  id       = each.value
}

data "aws_vpc" "this" {
  id = one(distinct([for subnet in data.aws_subnet.private : subnet.vpc_id]))
}

data "aws_route_table" "private" {
  for_each  = toset(var.private_subnet_ids)
  subnet_id = each.value
}

module "private_aws_api_connectivity" {
  source = "../../../../../modules/private-aws-api-connectivity"

  name            = "sumak-dev-eks"
  vpc_id          = data.aws_vpc.this.id
  vpc_cidr_block  = data.aws_vpc.this.cidr_block
  subnet_ids      = var.private_subnet_ids
  route_table_ids = distinct([for route_table in data.aws_route_table.private : route_table.id])

  tags = {
    Environment = "dev"
    Project     = "SUMAK"
    Tier        = "private-connectivity"
  }
}

module "control_plane" {
  source = "../../../../../modules/eks-control-plane"

  name               = "sumak-dev"
  cluster_role_arn   = var.cluster_role_arn
  cluster_version    = var.cluster_version
  private_subnet_ids = var.private_subnet_ids
  availability_zones = var.availability_zones

  tags = {
    Environment = "dev"
    Project     = "SUMAK"
    Tier        = "control-plane"
  }
}

module "managed_node_group" {
  source = "../../../../../modules/eks-managed-node-group"

  name               = "sumak-dev-general"
  cluster_name       = module.control_plane.cluster_name
  node_role_arn      = var.node_role_arn
  subnet_ids         = var.private_subnet_ids
  availability_zones = var.availability_zones
  root_volume_size   = var.root_volume_size

  depends_on = [module.private_aws_api_connectivity]

  tags = {
    Environment = "dev"
    Project     = "SUMAK"
    Tier        = "application"
  }
}
