terraform {
  backend "s3" {
    bucket = "rahul-mlops-data-bucket"
    key    = "terraform-state/deployment/terraform.tfstate"
    region = "us-east-1"
  }
}