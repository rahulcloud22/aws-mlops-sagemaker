locals {
  account_id = data.aws_caller_identity.current.account_id
  environment =  lower(var.environment)
}

resource "aws_sagemaker_model" "model" {
  name               = "rahul-${local.environment}-model-${var.github_run_id}"
  execution_role_arn = "arn:aws:iam::${local.account_id}:role/${var.sagemaker_execution_role}"
  primary_container {
    model_package_name = "arn:aws:sagemaker:us-east-1:${local.account_id}:model-package/${var.model_registry}/${var.model_version}"
  }
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_sagemaker_endpoint_configuration" "endpoint_config" {
  name = "rahul-${local.environment}-endpoint-config-${var.github_run_id}"
  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.model.name
    initial_instance_count = 1
    instance_type          = "ml.m5.xlarge"
  }
}

resource "aws_sagemaker_endpoint" "endpoint" {
  name                 = "rahul-${local.environment}-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.endpoint_config.name
  depends_on = [
    aws_sagemaker_endpoint_configuration.endpoint_config
  ]
}