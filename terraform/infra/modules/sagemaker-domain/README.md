# SageMaker Domain

Creates a SageMaker domain for ML development with Studio access and VPC integration.

## Usage

```hcl
module "sagemaker_domain" {
  source = "git::https://git.hrd-dev.com/HardRockDigital/terragrunt-modules//aws/sagemaker-domain?ref=v1.0.0"

  domain_name = "mlops-dev-domain"
  
  # VPC configuration
  vpc_id = dependency.vpc.outputs.vpc_id
  subnet_ids = dependency.vpc.outputs.private_subnet_ids
  security_group_ids = [dependency.sagemaker_security_group.outputs.security_group_id]
  
  # Domain settings
  auth_mode = "IAM"
  app_network_access_type = "VpcOnly"
  app_security_group_management = "Service"
  
  # Execution role
  execution_role_arn = "arn:aws:iam::711387121402:role/mlops-dev-sagemaker-execution-role"
  
  # Default user settings
  default_user_settings = {
    execution_role = "arn:aws:iam::711387121402:role/mlops-dev-sagemaker-execution-role"
    
    jupyter_server_app_settings = {
      default_resource_spec = {
        instance_type = "system"
        sagemaker_image_arn = "arn:aws:sagemaker:us-east-1:081325390199:image/jupyter-server-3"
      }
    }
    
    # Kernel Gateway (for custom kernels)
    kernel_gateway_app_settings = {
      default_resource_spec = {
        instance_type = "system"
        sagemaker_image_arn = "arn:aws:sagemaker:us-east-1:081325390199:image/kernel-gateway-3"
      }
    }
    
    # RStudio (if needed)
    r_session_app_settings = {
      default_resource_spec = {
        instance_type = "system"
        sagemaker_image_arn = "arn:aws:sagemaker:us-east-1:081325390199:image/rstudio-1"
      }
    }
  }
  
  tags = {
    Environment = "Development"
    Purpose     = "MLOps SageMaker Domain"
  }
}
```

## Instance Types

### System Instance Type
- **`instance_type = "system"`**: Required for SageMaker Studio
- Provides shared compute resources
- Automatically scales based on usage
- More cost-effective for development

### Custom Instance Types
For production workloads, you might want dedicated instances:
```hcl
instance_type = "ml.t3.medium"  # For dedicated compute
```

## Security Considerations

### IAM Authentication
- Uses IAM roles for authentication
- No need for separate user management
- Integrates with your existing IAM policies

### VPC-Only Access
- All traffic stays within your VPC
- Uses VPC endpoints for AWS service access
- No direct internet access from SageMaker apps

### Security Groups
- Automatically managed by AWS when using `app_security_group_management = "Service"`
- Allows traffic between SageMaker resources
- Restricts access to only necessary ports

## Cost Optimization

### System Instance Type
- Shared compute resources
- Pay only for actual usage
- Good for development and experimentation

### EFS Storage
- Shared storage across all users
- Pay for storage used
- Automatic scaling

### VPC Endpoints
- Can reduce data transfer costs
- More predictable pricing
- Better performance

## Troubleshooting

### Common Issues

1. **"Invalid instance type"**: Make sure to use `"system"` for SageMaker Studio
2. **"VPC not found"**: Ensure the VPC exists and is in the correct region
3. **"Subnet not found"**: Verify subnet IDs and availability zones
4. **"Execution role not found"**: Check that the IAM role exists and has proper permissions

### Debugging Commands

```bash
# Check domain status
aws sagemaker describe-domain --domain-id d-xxxxx

# List user profiles
aws sagemaker list-user-profiles --domain-id d-xxxxx

# Check VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=vpc-xxxxx"
```

### Network Connectivity

If users can't access SageMaker Studio:

1. **Check VPC endpoints**: Ensure all required endpoints are created
2. **Verify security groups**: Check that traffic is allowed
3. **Test DNS resolution**: Make sure private DNS is enabled
4. **Check route tables**: Verify traffic routing

## Dependencies

This module depends on:
- **VPC Infrastructure**: For networking components
- **IAM Role**: For execution permissions
- **VPC Endpoints**: For AWS service access

## Next Steps

After creating the domain:

1. **Create User Profiles**: Set up individual workspaces for team members
2. **Configure MLflow**: Set up experiment tracking
3. **Set up Model Registry**: Configure model versioning
4. **Create Pipelines**: Build ML workflows
5. **Configure Monitoring**: Set up model monitoring

## Contributing

When modifying this module:
1. Test instance type changes carefully
2. Verify security group configurations
3. Check VPC endpoint requirements
4. Update documentation for new features

<!-- BEGIN_TF_DOCS -->
## Resources

| Name | Type |
|------|------|
| [aws_sagemaker_domain.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_domain) | resource |
| [null_resource.wait_network](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource) | resource |

## Providers

| Name | Version |
|------|---------|
| aws | >=4.0.0, < 7.0.0 |
| null | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| account\_id | AWS Account ID | `string` | n/a | yes |
| account\_name | AWS Account name | `string` | n/a | yes |
| app\_network\_access\_type | The app network access type | `string` | `"PublicInternetOnly"` | no |
| app\_security\_group\_management | The app security group management | `string` | `"Service"` | no |
| auth\_mode | The authentication mode for the SageMaker domain | `string` | `"IAM"` | no |
| default\_user\_settings | Default user settings for the SageMaker domain | ```object({ execution_role = string jupyter_server_app_settings = optional(object({ default_resource_spec = object({ instance_type = string sagemaker_image_arn = string }) })) kernel_gateway_app_settings = optional(object({ default_resource_spec = object({ instance_type = string sagemaker_image_arn = string }) })) })``` | `null` | no |
| domain\_name | The name of the SageMaker domain | `string` | n/a | yes |
| enable\_jupyter\_server | Whether to enable Jupyter server app settings | `bool` | `true` | no |
| enable\_kernel\_gateway | Whether to enable kernel gateway app settings | `bool` | `false` | no |
| enable\_sharing\_settings | Whether to enable sharing settings | `bool` | `false` | no |
| environment | Environment name | `string` | n/a | yes |
| execution\_role\_arn | The ARN of the execution role for the SageMaker domain | `string` | n/a | yes |
| home\_efs\_file\_system\_retention | The retention policy for the home EFS file system | `string` | `"Delete"` | no |
| jupyter\_instance\_type | The instance type for Jupyter server | `string` | `"ml.t3.medium"` | no |
| jupyter\_sagemaker\_image\_arn | The ARN of the SageMaker image for Jupyter server | `string` | `""` | no |
| kernel\_gateway\_instance\_type | The instance type for kernel gateway | `string` | `"ml.t3.medium"` | no |
| kernel\_gateway\_sagemaker\_image\_arn | The ARN of the SageMaker image for kernel gateway | `string` | `""` | no |
| network\_ready\_id | ID of the network readiness resource that depends on all VPC endpoints | `string` | `null` | no |
| notebook\_output\_option | The notebook output option for sharing settings | `string` | `"Allowed"` | no |
| region | AWS Region name | `string` | `null` | no |
| s3\_kms\_key\_id | The KMS key ID for S3 output | `string` | `""` | no |
| s3\_output\_uri | The S3 output URI for sharing settings | `string` | `""` | no |
| security\_group\_ids | The security groups for the domain | `list(string)` | n/a | yes |
| studio\_web\_portal | Whether to enable the Studio web portal | `string` | `"ENABLED"` | no |
| subnet\_ids | The VPC subnets that the domain will use for communication between the domain and the VPC | `list(string)` | n/a | yes |
| tags | A map of tags to assign to the domain | `map(string)` | `{}` | no |
| terragrunt\_path | Path in the terragrunt repository | `string` | `null` | no |
| vpc\_id | The ID of the VPC that the domain will be created in | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| domain\_arn | The ARN of the SageMaker domain |
| domain\_id | The ID of the SageMaker domain |
| domain\_name | The name of the SageMaker domain |
| domain\_url | The URL of the SageMaker domain |
| home\_efs\_file\_system\_id | The ID of the home EFS file system |
| single\_sign\_on\_managed\_application\_instance\_id | The ID of the single sign-on managed application instance |
## Importing

```bash
terragrunt import aws_sagemaker_domain.this <domain-id>
```

<!-- END_TF_DOCS -->
