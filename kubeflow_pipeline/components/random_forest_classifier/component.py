from typing import NamedTuple

from kfp.components import create_component_from_func, InputPath, OutputPath


def rf_classifier(
    n_estimators: int,
    source_path: InputPath(str),
    model_path: OutputPath(str),
    mlpipeline_ui_metadata_path: OutputPath(str),
    mlpipeline_metrics_path: OutputPath("Metrics"),
) -> NamedTuple(
    "ClassificationOutput",
    [("mlpipeline_ui_metadata", "UI_metadata"), ("mlpipeline_metrics", "Metrics")],
):
    """training script for the random forest classifier"""
    import json
    import joblib

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_curve, accuracy_score, confusion_matrix
    from sklearn.model_selection import train_test_split
    import pandas as pd

    df = pd.read_csv(source_path)
    X = df.drop("target", axis=1)
    y = df["target"]
    # Binary classification problem for label 1.
    y = y == 1

    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
    rfc = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
    rfc.fit(X_train, y_train)

    y_test_predict = rfc.predict(X_test)
    accuracy = accuracy_score(y_test, y_test_predict)
    metrics = {
        "metrics": [
            {
                "name": "accuracy-score",  # The name of the metric. Visualized as the column name in the runs table.
                "numberValue": accuracy,  # The value of the metric. Must be a numeric value.
                "format": "PERCENTAGE",
                # The optional format of the metric. Supported values are "RAW" (displayed in raw format) and "PERCENTAGE" (displayed in percentage format).
            }
        ]
    }
    with open(mlpipeline_metrics_path, "w") as f:
        json.dump(metrics, f)

    metadata = {"outputs": []}

    y_scores = rfc.predict_proba(X_test)
    fpr, tpr, thresholds = roc_curve(
        y_true=y_test, y_score=y_scores[:, 1], pos_label=True
    )
    df_roc = pd.DataFrame({"fpr": fpr, "tpr": tpr, "thresholds": thresholds})
    metadata["outputs"].append(
        {
            "type": "roc",
            "format": "csv",
            "schema": [
                {"name": "fpr", "type": "NUMBER"},
                {"name": "tpr", "type": "NUMBER"},
                {"name": "thresholds", "type": "NUMBER"},
            ],
            "source": df_roc.to_csv(
                columns=["fpr", "tpr", "thresholds"], header=False, index=False
            ),
            "storage": "inline",
        },
    )

    confusion = confusion_matrix(y_test, y_test_predict)
    confusion_df = pd.DataFrame(confusion)
    confusion_df = (
        confusion_df.unstack()
        .reset_index()
        .rename({"level_0": "predicted", "level_1": "target", 0: "count"}, axis=1)
    )
    metadata["outputs"].append(
        {
            "type": "confusion_matrix",
            "format": "csv",
            "schema": [
                {"name": "target", "type": "CATEGORY"},
                {"name": "predicted", "type": "CATEGORY"},
                {"name": "count", "type": "NUMBER"},
            ],
            "source": confusion_df.to_csv(
                columns=["target", "predicted", "count"], header=False, index=False
            ),
            "storage": "inline",
            # Convert vocab to string because for bealean values we want "True|False" to match csv data.
            "labels": ["0", "1"],
        }
    )

    with open(mlpipeline_ui_metadata_path, "w") as metadata_file:
        json.dump(metadata, metadata_file)

    joblib.dump(rfc, model_path)

    return metadata, metrics


rf_classification_op = create_component_from_func(
    rf_classifier,
    packages_to_install=["scikit-learn==0.20.3", "pandas", "joblib==1.0.1"],
    base_image="python:3.7",
)

if __name__ == "__main__":
    rf_classifier(10, "wine_dataset.csv", "model", "metadata", "metrics")
