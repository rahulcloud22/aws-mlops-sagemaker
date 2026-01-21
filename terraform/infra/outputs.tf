output "vpc" {
  value = {
    id                = module.vpc.vpc_id
    public_subnet_ids = module.vpc.public_subnet_ids
    public_subnet_ids = module.vpc.public_subnet_ids
  }
}