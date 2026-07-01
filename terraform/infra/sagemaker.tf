
resource "aws_sagemaker_domain" "domain" {
  domain_name = "${var.application_name}-sagemaker-domain"
  auth_mode   = "IAM"
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.public_subnet_ids
  tags        = var.tags

  default_user_settings {
    execution_role      = aws_iam_role.sagemaker_execution_role.arn
    default_landing_uri = "studio::"
    studio_web_portal   = "ENABLED"
  }

  default_space_settings {
    execution_role = aws_iam_role.sagemaker_execution_role.arn
  }
}

resource "aws_sagemaker_user_profile" "user" {
  domain_id         = aws_sagemaker_domain.domain.id
  user_profile_name = "${var.application_name}-user-profile"
  tags              = var.tags
}

resource "aws_sagemaker_space" "jupyter_space" {
  domain_id          = aws_sagemaker_domain.domain.id
  space_name         = "jl-space-shared"
  space_display_name = "Shared JupyterLab Space"
  tags               = var.tags
  space_settings {
    app_type = "JupyterLab"
    jupyter_lab_app_settings {
      default_resource_spec {
        instance_type = "ml.t3.medium"
      }
    }
  }
  space_sharing_settings {
    sharing_type = "Shared"
  }
  ownership_settings {
    owner_user_profile_name = aws_sagemaker_user_profile.user.user_profile_name
  }
}

resource "aws_sagemaker_model_package_group" "model_package_group" {
  model_package_group_name = "${var.application_name}-model-package-group"
}