provider "aws" {
  region              = "us-east-1"
  profile             = "sumak-dev"
  allowed_account_ids = ["632080579751"]

  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "Terraform"
      Project     = "SUMAK"
      Stack       = "alb"
    }
  }
}

data "terraform_remote_state" "network_boundaries" {
  backend = "s3"
  config = {
    bucket       = "sumak-dev-tfstate-632080579751-us-east-1"
    key          = "us-east-1/dev/network-boundaries/terraform.tfstate"
    region       = "us-east-1"
    profile      = "sumak-dev"
    encrypt      = true
    use_lockfile = true
  }
}

module "alb" {
  source = "../../../../../modules/alb"

  name              = "sumak-dev"
  vpc_id            = data.terraform_remote_state.network_boundaries.outputs.network_vpc_id
  subnet_ids        = values(data.terraform_remote_state.network_boundaries.outputs.network_subnet_ids_by_tier["public"])
  security_group_id = [data.terraform_remote_state.network_boundaries.outputs.alb_security_group_id]

  listener_port         = var.listener_port
  target_port           = var.target_port
  target_protocol       = var.target_protocol
  health_check_path     = var.health_check_path
  health_check_interval = var.health_check_interval
  deregistration_delay  = var.deregistration_delay
  idle_timeout          = var.idle_timeout
  enable_https_listener = var.enable_https_listener
  certificate_arn       = var.certificate_arn

  tags = {
    Environment = "dev"
    Project     = "SUMAK"
    Tier        = "ingress"
  }
}
