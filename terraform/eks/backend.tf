terraform {
  backend "s3" {
    bucket       = "ml-inv-planner-one"
    key          = "eks/terraform.tfstate"
    region       = "eu-west-2"
    encrypt      = true
    use_lockfile = true
  }
}