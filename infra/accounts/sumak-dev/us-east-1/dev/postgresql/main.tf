provider "aws" {
  region              = "us-east-1"
  profile             = "sumak-dev"
  allowed_account_ids = ["632080579751"]

  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "Terraform"
      Project     = "SUMAK"
      Stack       = "private-postgresql"
    }
  }
}

module "private_postgresql" {
  source = "../../../../../modules/private-postgresql-capacity"

  name               = "rds-core-dev"
  vpc_id             = var.vpc_id
  private_subnet_ids = var.private_data_subnet_ids
  owner_security_group_ids = {
    identity = var.identity_service_security_group_id
    config   = var.config_service_security_group_id
  }

  tags = {
    Environment = "dev"
    Project     = "SUMAK"
    Scope       = "identity-config"
  }
}
