provider "aws" {
  region              = "us-east-1"
  profile             = "sumak-dev"
  allowed_account_ids = ["632080579751"]

  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "Terraform"
      Project     = "SUMAK"
      Stack       = "bastion"
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

module "private_ssm_bastion" {
  source = "../../../../../modules/private-ssm-bastion"

  name               = "sumak-dev"
  vpc_id             = data.terraform_remote_state.network.outputs.vpc_id
  vpc_cidr           = "10.10.0.0/16"
  subnet_id          = data.terraform_remote_state.network.outputs.subnet_ids_by_tier.application["us-east-1a"]
  private_subnet_ids = toset(values(data.terraform_remote_state.network.outputs.subnet_ids_by_tier.application))

  existing_running_ec2_count  = var.existing_running_ec2_count
  existing_running_vcpu_count = var.existing_running_vcpu_count

  tags = {
    Environment = "dev"
    Project     = "SUMAK"
  }
}
