import json
import logging
import pathlib
import pickle
import joblib
import tarfile
import pandas as pd
import os
import tarfile
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score

def is_within_directory(directory, target):         
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)

    prefix = os.path.commonprefix([abs_directory, abs_target])
    
    return prefix == abs_directory

def safe_extract(tar, path="."):
    for member in tar.getmembers():
        member_path = os.path.join(path, member.name)
        if not is_within_directory(path, member_path):
            raise Exception("Attempted Path Traversal in Tar File")
    tar.extractall(path) 

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

if __name__ == "__main__":
    logger.debug("Starting evaluation.")
    model_path = "/opt/ml/processing/model/model.tar.gz"

    with tarfile.open(model_path) as t:
      t.extractall()

    logger.debug("Loading model.")
    model = joblib.load(open("model.joblib", "rb"))
    tfidf = joblib.load(open("vectorizer.pkl", "rb"))

    logger.debug("Reading test data.")
    test_path = "/opt/ml/processing/test/test.csv"
    df = pd.read_csv(test_path)
    df['transformed_text'] = df['transformed_text'].fillna('').astype(str)

    y_test = df["target"]

    X_test = tfidf.transform(df['transformed_text'])

    logger.info("Performing predictions against test data.")
    predictions = model.predict(X_test)

    logger.debug("Calculating Metrics")

    accuracy = accuracy_score(y_test, predictions)
    conf_matrix = confusion_matrix(y_test, predictions)
    precision = precision_score(y_test, predictions)

    report_dict = {
        "binary_classification_metrics": {
            "accuracy": {
                "value" : accuracy,
                "standard_deviation": "NaN"
            },
            "confusion_matrix": {
                "0": {
                    "0": int(conf_matrix[0][0]),
                    "1": int(conf_matrix[0][1]),
                },
                "1": {
                    "0": int(conf_matrix[1][0]),
                    "1": int(conf_matrix[1][1]),
                },
            },
            "precision": {
                "value": precision,
                "standard_deviation": "NaN"
            }
        },
    }

    print(report_dict)

    output_dir = "/opt/ml/processing/evaluation"
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    logger.info("Writing out evaluation report")
    evaluation_path = f"{output_dir}/evaluation.json"
    with open(evaluation_path, "w") as f:
        f.write(json.dumps(report_dict))