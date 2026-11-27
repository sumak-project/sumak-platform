provider "aws" {
  region              = "us-east-1"
  profile             = "sumak-dev"
  allowed_account_ids = ["632080579751"]

  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "Terraform"
      Project     = "SUMAK"
      Stack       = "ecr"
    }
  }
}

module "identity_ecr" {
  source = "../../../../../modules/ecr-repository"

  repository_name = "sumak/dev/identity-svc"

  tags = {
    Artifact    = "identity-svc"
    Environment = "dev"
    Project     = "SUMAK"
  }
}
