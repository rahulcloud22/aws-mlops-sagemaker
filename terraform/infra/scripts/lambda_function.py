import requests
import json
import boto3
from botocore.exceptions import ClientError
import os

REGION_NAME = "us-east-1"
BRANCH = "code-test"

SAGEMAKER_PIPELINE_STATUS_EVENT = "SageMaker Model Building Pipeline Execution Status Change"
SAGEMAKER_MODEL_REGISTRY_EVENT = "SageMaker Model Package State Change"

client = boto3.client("secretsmanager", region_name=REGION_NAME)
sns_client = boto3.client("sns", region_name=REGION_NAME)

SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
SECRET_NAME = os.getenv("SECRET_NAME")

def publish_sns(message, subject):    
    print(message, subject)
    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject,
        Message=message
    )

def get_secret(secret_name, region_name):
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)
    except ClientError as e:
        print(f"Error fetching secret: {e}")
        raise e

def trigger_github_workflow(workflow, inputs):
    WORKFLOW_FILE = f"{workflow}.yaml"

    secret_data = get_secret(SECRET_NAME, REGION_NAME)
    GITHUB_TOKEN = secret_data.get("GITHUB_TOKEN")

    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "ref": BRANCH,
        "inputs": inputs
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 204:
        print("Workflow triggered successfully ✅")
    else:
        print("Failed to trigger workflow ❌")
        print(response.text)

def lambda_handler(event, context):
    if "Records" in event:
      print("S3 Event received:")
      record = event['Records'][0]
      bucket_name = record['s3']['bucket']['name']
      object_key = record['s3']['object']['key']

      print(f"[S3 EVENT] bucket={bucket_name} key={object_key}")

      s3_uri = f"s3://{bucket_name}/{object_key}"
      inputs = {
          "data_s3_uri": s3_uri
      }

      message = f"""
Pipeline Started Notification
-------------------------------
New Data: s3://{bucket_name}/{object_key}
"""

      trigger_github_workflow("start-ml-pipeline-test", inputs)
      publish_sns(message, subject=f"New ML Pipeline Started")



    if "detail-type" in event:
      print(f"SageMaker Event received: {event['detail-type']}")
      if event["detail-type"] == SAGEMAKER_PIPELINE_STATUS_EVENT:
          pipeline_name = event['detail']['pipelineArn'].split('/')[-1]
          message = f"""
Sagemaker Pipeline Notification
-------------------------------
Pipeline Name: {pipeline_name}
Execution Name: {event['detail']['pipelineExecutionDisplayName']}
Pipeline Status: {event['detail']['currentPipelineExecutionStatus']}
"""
          publish_sns(message, subject=f"Pipeline {event['detail']['currentPipelineExecutionStatus']}: {pipeline_name}")

      elif event["detail-type"] == SAGEMAKER_MODEL_REGISTRY_EVENT:
          model_approval_status = event['detail']['ModelApprovalStatus']
          model_registry = event['detail']['ModelPackageGroupName']
          model_version = event['detail']['ModelPackageVersion']
          github_run_id = event['detail']["ModelMetrics"]["ModelQuality"]["Statistics"]["S3Uri"].split("/")[3] if "ModelMetrics" in event['detail'] else "N/A"
          
          if "ModelLifeCycle" in event['detail']['UpdatedModelPackageFields']:
            print("ModelLifeCycle Event Triggered. No Action Required")
            print(event['detail']['UpdatedModelPackageFields'])
            return {"status": "ok"}
          
          if model_approval_status == 'Approved':
              inputs = {
                      "model_version": str(model_version),
                      "pipeline_github_id": github_run_id
                  }
              trigger_github_workflow("deployment-terraform-test", inputs)
          else:
              print("Model not approved.")

          message = f"""
Sagemaker Model Notification
-----------------------------
Model Registry: {model_registry}
Model Version: v{model_version}
Model Approval Status: {model_approval_status}
Approval Comment: {event['detail']['ApprovalDescription']}
Github Run ID: {github_run_id}
"""
          publish_sns(message, subject=f"Model {model_approval_status}: {model_registry}")
          
          return {"status": "ok"}