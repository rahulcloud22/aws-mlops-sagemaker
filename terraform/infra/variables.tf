variable "application_name" {
  default = "mlops"
}

variable "sns_subscribers" {
  type    = set(string)
  default = []
}

variable "sagemaker_pipeline_name" {
}

variable "repository_name" {
  description = "ORG/REPO"

}

variable "tags" {
  default = {}
}