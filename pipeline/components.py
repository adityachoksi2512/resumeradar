"""
ResumeRadar — Layer 7: Pipeline Orchestration (Prefect)
File: pipeline/components.py

Each function is a Prefect task — equivalent to a Vertex Pipeline component.
Tasks have typed inputs/outputs and can be cached, retried, and run in parallel.
"""

import pickle
import pandas as pd
from prefect import task
from prefect.cache_policies import INPUTS

from etl.data_processor import load_resumes
from ml.feature_engineering import build_features
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


@task(name="ingest-resumes", cache_policy=INPUTS)
def ingest(filepath: str, role: str) -> dict:
    """
    Component 1 — Ingest
    Loads the CSV and filters to the target role.
    Cached: re-running with the same file + role skips this step.
    """
    df = load_resumes(filepath)
    role_df = df[df["role_applied"] == role]
    print(f"[ingest] Loaded {len(role_df)} candidates for role='{role}'")
    return {"records": role_df.to_dict(orient="records"), "role": role}


@task(name="build-features", cache_policy=INPUTS)
def featurize(payload: dict) -> dict:
    """
    Component 2 — Feature Engineering
    Converts raw records into a numeric feature matrix.
    Cached: same payload = skip recomputation.
    """
    role = payload["role"]
    df = pd.DataFrame(payload["records"])
    df["skills_list"] = df["skills_raw"].str.split(", ")
    df["has_degree"] = df["has_degree"].astype(bool)

    feat_df = build_features(df, role)
    feature_cols = [c for c in feat_df.columns if c not in ["shortlisted", "candidate_id"]]

    print(f"[featurize] Built {len(feature_cols)} features for {len(feat_df)} candidates")
    return {
        "X": feat_df[feature_cols].values.tolist(),
        "y": feat_df["shortlisted"].tolist(),
        "feature_cols": feature_cols,
        "candidate_ids": feat_df["candidate_id"].tolist(),
        "role": role,
    }


@task(name="train-model")
def train(payload: dict) -> dict:
    """
    Component 3a — Train
    Trains a logistic regression model on the feature matrix.
    """
    import numpy as np
    X = np.array(payload["X"])
    y = np.array(payload["y"])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=200)
    model.fit(X_scaled, y)

    print(f"[train] Model trained on {len(X)} samples")
    return {
        "model": pickle.dumps(model).hex(),
        "scaler": pickle.dumps(scaler).hex(),
        "feature_cols": payload["feature_cols"],
        "role": payload["role"],
    }


@task(name="evaluate-model")
def evaluate(train_payload: dict, feat_payload: dict) -> dict:
    """
    Component 3b — Evaluate (runs in parallel with train)
    Computes accuracy on a held-out test split.
    """
    import numpy as np
    X = np.array(feat_payload["X"])
    y = np.array(feat_payload["y"])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    _, X_test, _, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=42)

    model = pickle.loads(bytes.fromhex(train_payload["model"]))
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"[evaluate] Accuracy: {acc:.0%}")
    return {"accuracy": round(acc, 4), "test_size": len(y_test)}


@task(name="save-model")
def save(train_payload: dict, eval_payload: dict, output_path: str) -> str:
    """
    Component 4 — Save
    Saves the model only if evaluation accuracy meets the threshold.
    Depends on both train and evaluate completing first.
    """
    acc = eval_payload["accuracy"]
    threshold = 0.7

    if acc < threshold:
        print(f"[save] Accuracy {acc:.0%} below threshold {threshold:.0%} — model not saved")
        return "skipped"

    model = pickle.loads(bytes.fromhex(train_payload["model"]))
    scaler = pickle.loads(bytes.fromhex(train_payload["scaler"]))

    with open(output_path, "wb") as f:
        pickle.dump({
            "model": model,
            "scaler": scaler,
            "features": train_payload["feature_cols"],
            "accuracy": acc,
        }, f)

    print(f"[save] Model saved to {output_path} (accuracy={acc:.0%})")
    return output_path
