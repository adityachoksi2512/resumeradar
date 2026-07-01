"""
ResumeRadar — Layer 7: Pipeline Orchestration (Prefect)
File: pipeline/pipeline.py

Defines the full ML pipeline as a Prefect flow.

Pipeline shape:
    ingest → featurize → train ──┐
                        └─ evaluate ──→ save

train and evaluate run in parallel after featurize completes.

Run with:
    python -m pipeline.pipeline
"""

from prefect import flow
from pipeline.components import ingest, featurize, train, evaluate, save
from prefect.futures import wait


@flow(name="resumeradar-ml-pipeline", log_prints=True)
def resumeradar_pipeline(
    filepath: str = "data/sample_resumes.csv",
    role: str = "ml_engineer",
    output_path: str = "models/model.pkl",
):
    print(f"\n{'='*55}")
    print(f"  ResumeRadar Pipeline — role={role}")
    print(f"{'='*55}\n")

    # Step 1 — Ingest (cached)
    raw = ingest(filepath, role)

    # Step 2 — Featurize (cached)
    features = featurize(raw)

    # Step 3 — Train and Evaluate in parallel
    train_result = train.submit(features)
    eval_result  = evaluate.submit(train_result, features)

    # Step 4 — Save (waits for both train + evaluate)
    saved_path = save(train_result, eval_result, output_path)

    print(f"\n{'='*55}")
    print(f"  Pipeline complete — model at: {saved_path}")
    print(f"{'='*55}\n")

    return saved_path


if __name__ == "__main__":
    resumeradar_pipeline()
