from sagemaker.core.helper.session_helper import Session, get_execution_role
from sagemaker.mlops.workflow.pipeline import Pipeline
from sagemaker.core.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.mlops.workflow.condition_step import ConditionStep
from sagemaker.core.workflow.functions import JsonGet
from sagemaker.mlops.workflow.steps import ProcessingStep, TrainingStep, CacheConfig, PropertyFile
from sagemaker.core.workflow.pipeline_context import PipelineSession
from sagemaker.train.model_trainer import ModelTrainer
from sagemaker.train.configs import  SourceCode, Compute, InputData
from sagemaker.mlops.workflow.model_step import ModelStep
from sagemaker.core.model_metrics import (ModelMetrics, MetricsSource)
from sagemaker.serve.model_builder import ModelBuilder
from sagemaker.core.shapes import OutputDataConfig
from sagemaker.core.workflow.pipeline_definition_config import PipelineDefinitionConfig
from sagemaker.serve.mode.function_pointers import Mode
from sagemaker.core.workflow.parameters import (
    ParameterInteger,
    ParameterFloat,
    ParameterString,
    ParameterBoolean,
)


from sagemaker.core.processing import (
    ScriptProcessor,
    FrameworkProcessor
)

from sagemaker.core.shapes import (
    ProcessingInput,
    ProcessingS3Input,
    ProcessingOutput,
    ProcessingS3Output
)
from sagemaker.core import image_uris

from sagemaker.serve.spec.inference_spec import InferenceSpec

import argparse

import yaml

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-s3-uri", type=str)
    parser.add_argument("--gh-run-id", type=str)
    parser.add_argument("--environment", type=str)
    args = parser.parse_args()

    gh_run_id = args.gh_run_id
    DATA_FILE_S3_URI= args.data_s3_uri
    environment = args.environment

    with open(f"config/{environment}/parameters.yaml", "r") as f:
        config = yaml.safe_load(f)

    APP_NAME = config["app"]["name"]
    version = config["app"]["version"].replace(".", "-")
    sagemaker_bucket = config["pipeline"]["sagemaker_bucket"]


    registry_name = config["model"]["RegistryName"]

    pipeline_parameters = config["pipeline"]["parameters"]

    base_job_prefix=f"{APP_NAME}-{environment}-{version}-{gh_run_id}"


    sagemaker_session = Session(
        default_bucket=sagemaker_bucket,
        default_bucket_prefix="sagemaker_session"
    )

    pipeline_session = PipelineSession(
        default_bucket=sagemaker_bucket,
        default_bucket_prefix="pipeline_session"
    )

    processing_instance_count = ParameterInteger(
        name="ProcessingInstanceCount", default_value=1
    )
    processing_instance_type = ParameterString(
        name="ProcessingInstanceType", default_value="ml.m5.medium"
    )
    training_instance_type = ParameterString(
        name="TrainingInstanceType", default_value="ml.m4.xlarge"
    )
    inference_instance_type = ParameterString(
        name="InferenceInstanceType", default_value="ml.m4.xlarge"
    )
    model_approval_status = ParameterString(
        name="ModelApprovalStatus", default_value="Approved"
    )

    # role = get_execution_role(sagemaker_session=sagemaker_session)
    # print(role)
    region = sagemaker_session.boto_region_name

    
    role="arn:aws:iam::853973692277:role/rahul-mlops-sagemaker-execution-role"


    # Cache Pipeline steps to reduce execution time on subsequent executions
    cache_config = CacheConfig(enable_caching=True, expire_after="2d")

    image_uri=image_uris.retrieve(
            framework="sklearn",
            region=region,
            version="1.2-1",
            py_version="py3",
        )

    sklearn_processor = FrameworkProcessor(
        image_uri=image_uri,
        instance_type=processing_instance_type,
        instance_count=1,
        base_job_name=f"{base_job_prefix}-preprocess",
        sagemaker_session=pipeline_session,
        role=role
    )

    preprocessor_args = sklearn_processor.run(
        source_dir="src",
        requirements="src/requirements.txt",
        code="src/preprocess.py",
        arguments=[
            "--input-path", "/opt/ml/processing/input/spam.csv",
            "--output-path", "/opt/ml/processing"
        ],
        inputs=[
        ProcessingInput(
            input_name="input-data",
                s3_input=ProcessingS3Input(
                    s3_uri=DATA_FILE_S3_URI,
                    local_path="/opt/ml/processing/input",
                    s3_data_type="S3Prefix",
                    s3_input_mode="File",
                    s3_data_distribution_type="FullyReplicated"
                )
            )
        ],
        outputs=[
        ProcessingOutput(
                output_name="train",
                s3_output=ProcessingS3Output(
                    s3_uri=f"s3://{sagemaker_session.default_bucket()}/{gh_run_id}/preprocessed-data/train", 
                    local_path="/opt/ml/processing/train",
                    s3_upload_mode="EndOfJob"
                )
            ),
            ProcessingOutput(
                output_name="test",
                s3_output=ProcessingS3Output(
                    s3_uri=f"s3://{sagemaker_session.default_bucket()}/{gh_run_id}/preprocessed-data/test",   
                    local_path="/opt/ml/processing/test",
                    s3_upload_mode="EndOfJob"
                )
            )]
    )

    step_preprocess = ProcessingStep(
        name="Step-1-Preprocess",
        step_args=preprocessor_args,
        cache_config=cache_config
    ) 

    model_trainer = ModelTrainer(
        training_image= image_uri,
        compute=Compute(
            instance_type=training_instance_type,
            instance_count=1,
        ),
        source_code=SourceCode(
            source_dir="src",
            entry_script="train.py"
        ),
        base_job_name=f"{base_job_prefix}-sklearn-train",
        sagemaker_session=pipeline_session,
        role=role,
        # hyperparameters={
        #     "objective": "reg:linear",
        #     "num_round": 50,
        #     "max_depth": 5
        # },
        input_data_config=[
            InputData(
                channel_name="train",
                data_source=step_preprocess.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri,
                content_type="text/csv"
            )
        ],
        output_data_config = OutputDataConfig(
            s3_output_path = f"s3://{sagemaker_session.default_bucket()}/{gh_run_id}/trained-model",
            remove_job_name_from_s3_output_path = True
        )
    )

    train_args = model_trainer.train()

    step_train = TrainingStep(
        name="Step-2-TrainModel",
        step_args=train_args,
        cache_config=cache_config,
        depends_on=[step_preprocess]
    )

    eval_processor = ScriptProcessor(
        image_uri=image_uri,
        command = ["python3"],
        instance_type=processing_instance_type,
        instance_count=processing_instance_count,
        base_job_name=f"{base_job_prefix}-evaluate-job",
        sagemaker_session=pipeline_session,
        role=role,
    )

    eval_processor_args = eval_processor.run(
        code="src/evaluate.py",
        inputs=[
                ProcessingInput(
                  input_name = "model",
                  s3_input=ProcessingS3Input(
                    s3_uri=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                    s3_data_type = "S3Prefix",
                    s3_input_mode="File",
                    local_path="/opt/ml/processing/model")
                ),
                ProcessingInput(
                  input_name = "test",
                  s3_input=ProcessingS3Input(
                    s3_uri=step_preprocess.properties.ProcessingOutputConfig.Outputs["test"].S3Output.S3Uri,
                    s3_data_type = "S3Prefix",
                    s3_input_mode="File",
                    local_path="/opt/ml/processing/test",
                ))
            ],
            outputs=[
                ProcessingOutput(
                    output_name="evaluation", 
                    s3_output=ProcessingS3Output(
                        s3_uri=f"s3://{sagemaker_session.default_bucket()}/{gh_run_id}/evaluation",
                        local_path="/opt/ml/processing/evaluation",
                        s3_upload_mode="EndOfJob"
                )),
            ],
    )

    evaluation_report = PropertyFile(
            name="EvaluationReport",
            output_name="evaluation",
            path="evaluation.json",
        )

    step_eval = ProcessingStep(
        name="Step-3-Evaluate",
        step_args=eval_processor_args,
        cache_config=cache_config,
        property_files=[evaluation_report],
        depends_on=[step_train]
    )

    model_metrics = ModelMetrics(
            model_statistics=MetricsSource(
                s3_uri="{}/evaluation.json".format(
                    step_eval.arguments["ProcessingOutputConfig"]["Outputs"][0]["S3Output"]["S3Uri"]
                ),
                content_type="application/json",
            )
        )

    model_builder = ModelBuilder(
        s3_model_data_url=step_train.properties.ModelArtifacts.S3ModelArtifacts,
        image_uri=image_uri,
        sagemaker_session=pipeline_session,
        role_arn=role,
        source_code=SourceCode(
            source_dir="src",
            entry_script="inference.py"
        ))
        
    step_create_model = ModelStep(
        name="Step-5-Create-Model",
        step_args=model_builder.build(
            model_name=base_job_prefix #'modelName' must satisfy regular expression pattern: [a-zA-Z0-9]([\-a-zA-Z0-9]*[a-zA-Z0-9])?
        )
    )

    step_register_model = ModelStep(
        name="Step-6-Register-Model",
        step_args=model_builder.register(
            model_package_group_name=registry_name,
            content_types=["application/json"],
            response_types=["application/json"],
            inference_instances=[inference_instance_type],
            approval_status=model_approval_status,
            model_metrics=model_metrics
        ),
        depends_on=[step_create_model]
    )

    # step_deploy_model = ModelStep(
    #     name="Step-7-Deploy-Model",
    #     step_args=model_builder.deploy(
    #         endpoint_name="rahul-mlops-test-endpoint",
    #         update_endpoint=True
    #     ),
    #     depends_on=[step_register_model]
    # )


    cond_gte = ConditionGreaterThanOrEqualTo(
            left=JsonGet(
                step_name=step_eval.name,
                property_file=evaluation_report,
                json_path="binary_classification_metrics.precision.value",
            ),
            right=0.95,
        )
    
    step_cond = ConditionStep(
            name="Step-4-Metrics-Evaluation",
            conditions=[cond_gte],
            if_steps=[step_create_model,step_register_model],
            else_steps=[],
        )

    pipeline = Pipeline(
        name="rahul-mlops-pipeline",
        parameters=[
            processing_instance_type,
            processing_instance_count,
            training_instance_type,
            inference_instance_type,
            model_approval_status
        ],
        steps=[step_preprocess,step_train, step_eval,step_cond],
        sagemaker_session=sagemaker_session,
        pipeline_definition_config=PipelineDefinitionConfig(
            use_custom_job_prefix=True
        )
    )

    pipeline.upsert(role_arn=role)
    execution = pipeline.start(
        execution_display_name = f"execution-{gh_run_id}",
        parameters=pipeline_parameters
    )
    print(f"\n###### Execution started with PipelineExecutionArn: {execution.arn}")

    print("Waiting for the execution to finish...")
    # execution.wait()
    # print("\n#####Execution completed. Execution step details:")

    pipeline_steps = execution.list_steps()
    print(pipeline_steps)

if __name__ == "__main__":
    main()