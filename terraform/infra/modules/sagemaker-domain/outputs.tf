output "domain_id" {
  description = "The ID of the SageMaker domain"
  value       = aws_sagemaker_domain.this.id
}

output "domain_arn" {
  description = "The ARN of the SageMaker domain"
  value       = aws_sagemaker_domain.this.arn
}

output "domain_name" {
  description = "The name of the SageMaker domain"
  value       = aws_sagemaker_domain.this.domain_name
}

output "domain_url" {
  description = "The URL of the SageMaker domain"
  value       = aws_sagemaker_domain.this.url
}

output "home_efs_file_system_id" {
  description = "The ID of the home EFS file system"
  value       = aws_sagemaker_domain.this.home_efs_file_system_id
}

output "single_sign_on_managed_application_instance_id" {
  description = "The ID of the single sign-on managed application instance"
  value       = aws_sagemaker_domain.this.single_sign_on_managed_application_instance_id
}
