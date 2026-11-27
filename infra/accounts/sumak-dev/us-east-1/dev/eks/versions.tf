terraform {
  required_version = ">= 1.10.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket       = "sumak-dev-tfstate-632080579751-us-east-1"
    key          = "us-east-1/dev/eks/terraform.tfstate"
    region       = "us-east-1"
    profile      = "sumak-dev"
    encrypt      = true
    use_lockfile = true
  }
}
