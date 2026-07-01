import joblib
import os
import json
import tarfile

"""
Deserialize fitted model
"""
def model_fn(model_dir):
    # model_path = "/opt/ml/model/model.tar.gz"

    # # with tarfile.open(model_path) as t:
    # #   t.extractall()
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    vectorizer = joblib.load(os.path.join(model_dir, "vectorizer.pkl"))
    return model,vectorizer

"""
input_fn
    request_body: The body of the request sent to the model.
    request_content_type: (string) specifies the format/variable type of the request
"""
def input_fn(request_body, request_content_type):
    """Parse input data"""
    if request_content_type == "application/json":
        data = json.loads(request_body)
        return data["text"]
    elif request_content_type == "text/plain":
        return request_body
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")


def predict_fn(input_data, model):
    """Run prediction"""
    clf, vectorizer = model
    X = vectorizer.transform([input_data])
    prediction = clf.predict(X)
    return int(prediction[0])


def output_fn(prediction, response_content_type):
    """Format output"""
    if response_content_type == "application/json":
        return json.dumps({"prediction": prediction})
    elif response_content_type == "text/plain":
        return str(prediction)
    else:
        raise ValueError(f"Unsupported response type: {response_content_type}")