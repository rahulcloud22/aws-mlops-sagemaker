terraform {
  #terraform init -migrate-state -force-copy
  #copies local state to remote backend store the current configuration with no changes to the state
  # terraform init -reconfigure
  backend "s3" {}
}