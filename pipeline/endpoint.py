import boto3

PIPELINE_EXECUTION_ARN = "arn:aws:sagemaker:us-east-1:853973692277:pipeline/rahul-mlops-pipeline/execution/wfsxb607q5zf"

sagemaker = boto3.client("sagemaker")

response = sagemaker.describe_pipeline_execution(
    PipelineExecutionArn=PIPELINE_EXECUTION_ARN
)

# Print all outputs (optional, for debugging)
print(response)

# # Extract the model name
# model_name = next(
#     output["Value"]
#     for output in response["PipelineExecutionOutputs"]
#     if output["Name"] == "CreatedModelName"
# )

# print("Created model name:", model_name)