# Network readiness check
resource "null_resource" "wait_network" {
  count = var.network_ready_id != null ? 1 : 0

  triggers = {
    network_ready_id = var.network_ready_id
  }
}

# SageMaker Domain resource
resource "aws_sagemaker_domain" "this" {
  domain_name = var.domain_name
  auth_mode   = var.auth_mode
  vpc_id      = var.vpc_id
  subnet_ids  = var.subnet_ids

  # Wait for network to be ready
  depends_on = [null_resource.wait_network]

  dynamic "default_user_settings" {
    for_each = var.default_user_settings != null ? [var.default_user_settings] : []
    content {
      execution_role  = default_user_settings.value.execution_role
      security_groups = var.security_group_ids

      dynamic "jupyter_server_app_settings" {
        for_each = default_user_settings.value.jupyter_server_app_settings != null ? [default_user_settings.value.jupyter_server_app_settings] : []
        content {
          default_resource_spec {
            instance_type       = jupyter_server_app_settings.value.default_resource_spec.instance_type
            sagemaker_image_arn = jupyter_server_app_settings.value.default_resource_spec.sagemaker_image_arn
          }
        }
      }

      dynamic "kernel_gateway_app_settings" {
        for_each = default_user_settings.value.kernel_gateway_app_settings != null ? [default_user_settings.value.kernel_gateway_app_settings] : []
        content {
          default_resource_spec {
            instance_type       = kernel_gateway_app_settings.value.default_resource_spec.instance_type
            sagemaker_image_arn = kernel_gateway_app_settings.value.default_resource_spec.sagemaker_image_arn
          }
        }
      }
    }
  }

  # Fallback to old structure if default_user_settings is not provided
  dynamic "default_user_settings" {
    for_each = var.default_user_settings == null ? [1] : []
    content {
      execution_role  = var.execution_role_arn
      security_groups = var.security_group_ids

      dynamic "jupyter_server_app_settings" {
        for_each = var.enable_jupyter_server ? [1] : []
        content {
          default_resource_spec {
            instance_type       = var.jupyter_instance_type
            sagemaker_image_arn = var.jupyter_sagemaker_image_arn != "" ? var.jupyter_sagemaker_image_arn : null
          }
        }
      }

      dynamic "kernel_gateway_app_settings" {
        for_each = var.enable_kernel_gateway ? [1] : []
        content {
          default_resource_spec {
            instance_type       = var.kernel_gateway_instance_type
            sagemaker_image_arn = var.kernel_gateway_sagemaker_image_arn != "" ? var.kernel_gateway_sagemaker_image_arn : null
          }
        }
      }

      dynamic "sharing_settings" {
        for_each = var.enable_sharing_settings ? [1] : []
        content {
          notebook_output_option = var.notebook_output_option
          s3_kms_key_id          = var.s3_kms_key_id != "" ? var.s3_kms_key_id : null
          s3_output_path         = var.s3_output_uri != "" ? var.s3_output_uri : null
        }
      }

      studio_web_portal = var.studio_web_portal
    }
  }

  app_network_access_type       = var.app_network_access_type
  app_security_group_management = var.app_security_group_management

  dynamic "retention_policy" {
    for_each = var.home_efs_file_system_retention != "Delete" ? [1] : []
    content {
      home_efs_file_system = var.home_efs_file_system_retention
    }
  }

  tags = var.tags
}
