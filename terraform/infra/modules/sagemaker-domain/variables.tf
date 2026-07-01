variable "domain_name" {
  type        = string
  description = "The name of the SageMaker domain"
}

variable "auth_mode" {
  type        = string
  description = "The authentication mode for the SageMaker domain"
  default     = "IAM"
  validation {
    condition     = contains(["IAM", "SSO"], var.auth_mode)
    error_message = "Auth mode must be either 'IAM' or 'SSO'."
  }
}

variable "vpc_id" {
  type        = string
  description = "The ID of the VPC that the domain will be created in"
}

variable "subnet_ids" {
  type        = list(string)
  description = "The VPC subnets that the domain will use for communication between the domain and the VPC"
}

variable "execution_role_arn" {
  type        = string
  description = "The ARN of the execution role for the SageMaker domain"
}

variable "security_group_ids" {
  type        = list(string)
  description = "The security groups for the domain"
}

variable "enable_jupyter_server" {
  type        = bool
  description = "Whether to enable Jupyter server app settings"
  default     = true
}

variable "jupyter_instance_type" {
  type        = string
  description = "The instance type for Jupyter server"
  default     = "ml.t3.medium"
}

variable "jupyter_sagemaker_image_arn" {
  type        = string
  description = "The ARN of the SageMaker image for Jupyter server"
  default     = ""
}

variable "enable_kernel_gateway" {
  type        = bool
  description = "Whether to enable kernel gateway app settings"
  default     = false
}

variable "kernel_gateway_instance_type" {
  type        = string
  description = "The instance type for kernel gateway"
  default     = "ml.t3.medium"
}

variable "kernel_gateway_sagemaker_image_arn" {
  type        = string
  description = "The ARN of the SageMaker image for kernel gateway"
  default     = ""
}

variable "enable_sharing_settings" {
  type        = bool
  description = "Whether to enable sharing settings"
  default     = false
}

variable "notebook_output_option" {
  type        = string
  description = "The notebook output option for sharing settings"
  default     = "Allowed"
  validation {
    condition     = contains(["Allowed", "Disabled"], var.notebook_output_option)
    error_message = "Notebook output option must be either 'Allowed' or 'Disabled'."
  }
}

variable "s3_kms_key_id" {
  type        = string
  description = "The KMS key ID for S3 output"
  default     = ""
}

variable "s3_output_uri" {
  type        = string
  description = "The S3 output URI for sharing settings"
  default     = ""
}

variable "studio_web_portal" {
  type        = string
  description = "Whether to enable the Studio web portal"
  default     = "ENABLED"
  validation {
    condition     = contains(["ENABLED", "DISABLED"], var.studio_web_portal)
    error_message = "Studio web portal must be either 'ENABLED' or 'DISABLED'."
  }
}

variable "app_network_access_type" {
  type        = string
  description = "The app network access type"
  default     = "VpcOnly"
  validation {
    condition     = contains(["PublicInternetOnly", "VpcOnly"], var.app_network_access_type)
    error_message = "App network access type must be either 'PublicInternetOnly' or 'VpcOnly'."
  }
}

variable "app_security_group_management" {
  type        = string
  description = "The app security group management"
  default     = "Service"
  validation {
    condition     = contains(["Service", "Customer"], var.app_security_group_management)
    error_message = "App security group management must be either 'Service' or 'Customer'."
  }
}

variable "home_efs_file_system_retention" {
  type        = string
  description = "The retention policy for the home EFS file system"
  default     = "Delete"
  validation {
    condition     = contains(["Delete", "Retain"], var.home_efs_file_system_retention)
    error_message = "Home EFS file system retention must be either 'Delete' or 'Retain'."
  }
}

variable "tags" {
  type        = map(string)
  description = "A map of tags to assign to the domain"
  default     = {}
}

variable "network_ready_id" {
  type        = string
  description = "ID of the network readiness resource that depends on all VPC endpoints"
  default     = null
}

variable "default_user_settings" {
  type = object({
    execution_role = string
    jupyter_server_app_settings = optional(object({
      default_resource_spec = object({
        instance_type       = string
        sagemaker_image_arn = string
      })
    }))
    kernel_gateway_app_settings = optional(object({
      default_resource_spec = object({
        instance_type       = string
        sagemaker_image_arn = string
      })
    }))
  })
  description = "Default user settings for the SageMaker domain"
  default     = null
}


