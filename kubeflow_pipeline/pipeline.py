import os
import yaml
from kfp import dsl, Client
from kfp.aws import use_aws_secret
from kfp.components import load_component_from_file, ComponentStore
from components.random_forest_classifier.component import rf_classification_op
from components.validate.component import validate_csv_op
from dotenv import load_dotenv

load_dotenv()

s3_yaml_path = "components/read_from_s3/component.yaml"
s3_download_op = load_component_from_file(s3_yaml_path)

s3_upload_yaml_path = "components/write_to_s3/component.yaml"
s3_upload_op = load_component_from_file(s3_upload_yaml_path)

store: ComponentStore = ComponentStore.default_store
kfserving_op = store.load_component("kubeflow/kfserving")


@dsl.pipeline(
    name="wine-classification", description="A pipeline training wine CSV model."
)
def example_random_forest_pipeline(
    inp_s3_uri: str, random_forest_estimators: int, out_model_s3_uri: str
):
    # step 01: read the data from s3
    s3_download = s3_download_op(s3_uri=inp_s3_uri).apply(use_aws_secret())

    # step 02: data validation step
    exp_suite_path = os.path.join("components", "validate", "expectation_suite.json")
    with open(exp_suite_path) as file:
        exp_suite = file.read()
    validate_csv = validate_csv_op(csv=s3_download.output, expectation_suite=exp_suite)

    # step 03: random forest classifier
    wine_classification = rf_classification_op(
        source=s3_download.output, n_estimators=random_forest_estimators
    ).after(validate_csv)

    # step 04: Upload the file to s3
    s3_upload = s3_upload_op(
        input_path=wine_classification.outputs["model"],
        s3_uri=f"{out_model_s3_uri}/{{{{workflow.namespace}}}}/{{{{workflow.name}}}}",
        s3_filename="model.joblib",
        extra_cp_opts="",
    ).apply(use_aws_secret())

    # step 04: serve the model
    inference_spec = {
        "apiVersion": "serving.kubeflow.org/v1beta1",
        "kind": "InferenceService",
        "metadata": {},
        "spec": {
            "predictor": {
                "canaryTrafficPercent": 100,
                "sklearn": {
                    "name": "kfserving-container",
                    "protocolVersion": "v1",
                    "resources": {
                        "limits": {"cpu": "1", "memory": "2Gi"},
                        "requests": {"cpu": "1", "memory": "2Gi"},
                    },
                    "runtimeVersion": "v0.6.1",
                    "storageUri": s3_upload.output.pattern,
                },
                "timeout": 60,
            }
        },
    }

    kfserving_op(
        action="apply",
        model_name="wine-classification",
        namespace="kubeflow-user-example-com",
        inferenceservice_yaml=yaml.safe_dump(inference_spec),
    )


if __name__ == "__main__":

    kubeflow_gateway_endpoint = os.environ.get("KUBEFLOW_GATEWAY_ENDPOINT_LOCALHOST")
    authservice_session_cookie = os.environ.get("KUBEFLOW_COOKIE_LOCALHOST")
    env = "innov8"  # 'sandbox'
    host = None
    if kubeflow_gateway_endpoint:
        host = f"http://{kubeflow_gateway_endpoint}/pipeline"

    cookies = None
    if authservice_session_cookie:
        cookies = f"authservice_session={authservice_session_cookie}"

    client = Client(host=host, cookies=cookies)
    n_estimators = 6
    client.create_run_from_pipeline_func(
        example_random_forest_pipeline,
        namespace="kubeflow-user-example-com",
        arguments={
            "inp_s3_uri": f"s3://kubeflow-{env}-nbi/wine_dataset.csv",
            "out_model_s3_uri": f"s3://kubeflow-{env}-nbi/models",
            "random_forest_estimators": n_estimators,
        },
        experiment_name="random_forest_estimator",
    )
