locals {}

module "vpc" {
  source           = "./modules/vpc"
  application_name = var.application_name
  vpc_cidr         = "10.0"
  tags             = var.tags
}

resource "aws_s3_bucket" "data_bucket" {
  bucket = "${var.application_name}-data-bucket"
  tags   = var.tags
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.data_bucket.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.sagemaker_event_handler.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "cleaned_data/"
    filter_suffix       = ".csv"
  }
  depends_on = [
    aws_lambda_permission.allow_s3
  ]
}

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/scripts/lambda_function.py"
  output_path = "${path.module}/scripts/lambda.zip"
}

resource "aws_lambda_function" "sagemaker_event_handler" {
  function_name    = "${var.application_name}-sagemaker-model-handler"
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.14"
  handler          = "lambda_function.lambda_handler"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  depends_on       = [data.archive_file.lambda_zip]
  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.pipeline_notifications.arn
      SECRET_NAME = aws_secretsmanager_secret.mlops_secret.name
      GITHUB_REPO   = var.repository_name
    }
  }
  layers = ["arn:aws:lambda:us-east-1:853973692277:layer:azeem_layer:1"]
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.sagemaker_event_handler.function_name}"
  retention_in_days = 1
  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.sagemaker_model_package_state_change.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.sagemaker_event_handler.arn
  role_arn  = aws_iam_role.lambda_role.arn
}

resource "aws_cloudwatch_event_target" "pipeline_lambda_target" {
  rule      = aws_cloudwatch_event_rule.sagemaker_pipeline_execution.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.sagemaker_event_handler.arn
  role_arn  = aws_iam_role.lambda_role.arn
}

resource "aws_cloudwatch_event_rule" "sagemaker_model_package_state_change" {
  name        = "${var.application_name}-sagemaker-model-package-state-change"
  description = "Triggers on SageMaker Model Package state changes"

  event_pattern = jsonencode({
    source        = ["aws.sagemaker"]
    "detail-type" = ["SageMaker Model Package State Change"]
    detail = {
      "ModelPackageGroupName" : [aws_sagemaker_model_package_group.model_package_group.model_package_group_name]
    }
  })
}

resource "aws_cloudwatch_event_rule" "sagemaker_pipeline_execution" {
  name        = "${var.application_name}-sagemaker-pipeline-execution"
  description = "Tracks SageMaker Pipeline execution state changes"
  event_pattern = jsonencode({
    source        = ["aws.sagemaker"]
    "detail-type" = ["SageMaker Model Building Pipeline Execution Status Change"],
    detail = {
      "pipelineArn" : ["arn:aws:sagemaker:us-east-1:${data.aws_caller_identity.current.account_id}:pipeline/${var.sagemaker_pipeline_name}"]
      # currentPipelineExecutionStatus = [
      #   "Succeeded",
      #   "Failed",
      #   "Stopped",
      #   "Executing"
      # ]
    }
  })
}

resource "aws_sns_topic" "pipeline_notifications" {
  name = "${var.application_name}-pipeline-notifications"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  for_each  = var.sns_subscribers
  topic_arn = aws_sns_topic.pipeline_notifications.arn
  protocol  = "email"
  endpoint  = each.value
}

resource "aws_secretsmanager_secret" "mlops_secret" {
  name        = "${var.application_name}-secret"
  description = "This is a secret for MLOps project"
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sagemaker_event_handler.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data_bucket.arn
}