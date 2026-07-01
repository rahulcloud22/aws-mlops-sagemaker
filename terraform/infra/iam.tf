
resource "aws_iam_role" "github_role" {
  name               = "${var.application_name}-github-role"
  assume_role_policy = data.aws_iam_policy_document.github_role_trust_policy.json
}

resource "aws_iam_role_policy" "sagemaker_pipeline_inline" {
  name = "github-sagemaker-pipeline-inline-policy"
  role = aws_iam_role.github_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SageMakerPipelineExecution"
        Effect = "Allow"
        Action = [
          "sagemaker:StartPipelineExecution",
          "sagemaker:DescribePipelineExecution",
          "sagemaker:ListPipelineExecutions",
          "sagemaker:ListPipelineExecutionSteps",
          "sagemaker:DescribePipeline",
          "sagemaker:CreatePipeline",
          "sagemaker:UpdatePipeline"
        ]
        Resource = [
          "arn:aws:sagemaker:us-east-1:${data.aws_caller_identity.current.account_id}:pipeline/${var.sagemaker_pipeline_name}",
          "arn:aws:sagemaker:us-east-1:${data.aws_caller_identity.current.account_id}:pipeline/${var.sagemaker_pipeline_name}/execution/*"
        ]
      },
      {
        Sid    = "AllowSageMakerListBucket",
        Effect = "Allow",
        Action = [
          "s3:ListBucket",
          "s3:GetObject", # to read tf.state
          "s3:PutObject"  # required to upload src code to s3
        ],
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.data_bucket.id}",
          "arn:aws:s3:::${aws_s3_bucket.data_bucket.id}/*"
        ]
      },
      {
        Sid      = "PassExecutionRole"
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.sagemaker_execution_role.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "github_sagemaker_terraform" {
  name = "github-sagemaker-terraform-inline-policy"
  role = aws_iam_role.github_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:CreateModel",
          "sagemaker:DescribeModel",
          "sagemaker:DeleteModel",
          "sagemaker:CreateEndpointConfig",
          "sagemaker:DescribeEndpointConfig",
          "sagemaker:DeleteEndpointConfig",
          "sagemaker:CreateEndpoint",
          "sagemaker:DescribeEndpoint",
          "sagemaker:UpdateEndpoint",
          "sagemaker:DeleteEndpoint",
          "sagemaker:DescribeModelPackage",
          "sagemaker:UpdateModelPackage",
          "sagemaker:ListModelPackages",
          "sagemaker:ListTags",
          "SageMaker:DeleteTags",
          "SageMaker:CreateTags"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "sagemaker_execution_role" {
  name = "${var.application_name}-sagemaker-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sagemaker_execution_role" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy" "allow_data_s3" {
  name = "get-specific-s3-object"
  role = aws_iam_role.sagemaker_execution_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.data_bucket.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.application_name}-sagemaker-event-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
      },
      {
        "Sid" : "TrustEventBridgeService",
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "events.amazonaws.com"
        },
        "Action" : "sts:AssumeRole",
        "Condition" : {
          "StringEquals" : {
            "aws:SourceArn" : aws_cloudwatch_event_rule.sagemaker_model_package_state_change.arn,
            "aws:SourceAccount" : data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "eventbridge_inline_policy" {
  name = "${var.application_name}-eventbridge-invoke-lambda-and-logs"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "InvokeSpecificLambda"
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.sagemaker_event_handler.arn
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Sid    = "GetSecretValue"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.mlops_secret.arn
      },
      {
        Sid      = "AllowSnsPublish"
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.pipeline_notifications.arn
      }
    ]
  })
}