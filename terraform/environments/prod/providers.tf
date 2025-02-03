terraform {
  required_version = "1.10.4"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 5.84.0"
    }
  }
}

# https://developer.hashicorp.com/terraform/language/providers/configuration
provider "aws" {
  region = "ap-northeast-1"
  default_tags {
    tags = {
      terraform = "true"
      project   = "household_account_book"
      env       = var.env
    }
  }
}
