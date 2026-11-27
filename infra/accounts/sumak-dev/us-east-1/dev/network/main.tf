provider "aws" {
  region              = "us-east-1"
  profile             = "academy"
  allowed_account_ids = ["632080579751"]

  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "Terraform"
      Project     = "SUMAK"
      Stack       = "network"
    }
  }
}

module "dev_vpc" {
  source = "../../../../../modules/vpc"

  name     = "sumak-dev"
  vpc_cidr = "10.10.0.0/16"

  availability_zones = {
    us-east-1a = {
      zone_id          = "use1-az2"
      public_cidr      = "10.10.0.0/20"
      application_cidr = "10.10.64.0/20"
      data_cidr        = "10.10.128.0/20"
    }
    us-east-1b = {
      zone_id          = "use1-az4"
      public_cidr      = "10.10.16.0/20"
      application_cidr = "10.10.80.0/20"
      data_cidr        = "10.10.144.0/20"
    }
    us-east-1c = {
      zone_id          = "use1-az6"
      public_cidr      = "10.10.32.0/20"
      application_cidr = "10.10.96.0/20"
      data_cidr        = "10.10.160.0/20"
    }
  }

  tags = {
    Environment = "dev"
    Project     = "SUMAK"
  }
}
