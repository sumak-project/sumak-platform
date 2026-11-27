provider "aws" {
  region              = "us-east-1"
  profile             = "sumak-dev"
  allowed_account_ids = ["632080579751"]
  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "Terraform"
      Project     = "SUMAK"
      Stack       = "network-boundaries"
    }
  }
}

data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket       = "sumak-dev-tfstate-632080579751-us-east-1"
    key          = "us-east-1/dev/network/terraform.tfstate"
    region       = "us-east-1"
    profile      = "sumak-dev"
    encrypt      = true
    use_lockfile = true
  }
}

module "network_security_groups" {
  source = "../../../../../modules/network-security-groups"

  name_prefix                = "sumak-dev"
  vpc_id                     = data.terraform_remote_state.network.outputs.vpc_id
  allowed_ingress_ipv4_cidrs = var.allowed_ingress_ipv4_cidrs
  allowed_ingress_ipv6_cidrs = var.allowed_ingress_ipv6_cidrs
  alb_listener_port          = var.alb_listener_port
  gateway_port               = var.gateway_port
  bff_port                   = var.bff_port
  services                   = var.services
  brokers                    = var.brokers
  management_endpoints       = var.management_endpoints

  tags = {
    Environment = "dev"
    Project     = "SUMAK"
  }
}
