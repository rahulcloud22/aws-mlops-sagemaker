variable "model_version" {
  type = string
}

variable "github_run_id" {
  type = string
}

variable "environment" {
  type = string
}

variable "model_registry" {
  type    = string
  default = "rahul-mlops-model-package-group"
}

variable "sagemaker_execution_role" {
  type    = string
  default = "rahul-mlops-sagemaker-execution-role"
}
