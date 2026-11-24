provider "aws" {
  region              = "us-east-1"
  profile             = "academy"
  allowed_account_ids = ["632080579751"]

  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "Terraform"
      Project     = "SUMAK"
      Stack       = "state-backend"
    }
  }
}

provider "awscc" {
  region  = "us-east-1"
  profile = "academy"
}

module "state_backend" {
  source = "../../../../../modules/terraform-state-backend"

  bucket_name = "sumak-dev-tfstate-632080579751-us-east-1"

  tags = {
    DataClassification = "InfrastructureState"
    Environment        = "dev"
    ManagedBy          = "Terraform"
    Project            = "SUMAK"
    Stack              = "state-backend"
  }
}

import {
  to = module.state_backend.awscc_s3_bucket.this
  id = "sumak-dev-tfstate-632080579751-us-east-1"
}
