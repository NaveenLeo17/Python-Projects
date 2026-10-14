"""End-to-end training: preprocess -> TF-IDF -> tune several models -> evaluate -> save best."""
import json
import time
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (GridSearchCV, ParameterGrid, RandomizedSearchCV,
                                     StratifiedKFold, train_test_split)

from . import config
from .data_loader import load_dataset
from .evaluate import (compute_metrics, get_scores, plot_confusion_matrix,
                       plot_model_comparison, plot_roc_curves, plot_top_features,
                       top_features)
from .features import build_pipeline
from .models import get_model_specs
from .preprocessing import TextPreprocessor, backend_info

NORMALIZERS = {  # name -> (stemming, lemmatization)
    "none": (False, False),
    "stem": (True, False),
    "lemma": (False, True),
    "both": (True, True),
}


def make_preprocessor(normalizer):
    stem, lemma = NORMALIZERS[normalizer]
    return TextPreprocessor(remove_stopwords=True, stemming=stem, lemmatization=lemma)


def _log(msg, verbose):
    if verbose:
        print(msg, flush=True)


def _preprocess_frame(df, preprocessor):
    out = df.copy()
    out["clean"] = preprocessor.transform(out["text"])
    return out[out["clean"].str.len() > 0]


def compare_preprocessing(train_df, test_df, verbose=True):
    """Same baseline model (logistic regression) under each normalisation strategy."""
    rows = []
    for name in NORMALIZERS:
        t0 = time.time()
        pre = make_preprocessor(name)
        tr, te = _preprocess_frame(train_df, pre), _preprocess_frame(test_df, pre)
        prep_seconds = time.time() - t0
        pipe = build_pipeline(LogisticRegression(max_iter=1000,
                                                 random_state=config.RANDOM_STATE))
        pipe.fit(tr["clean"], tr["label"])
        pred = pipe.predict(te["clean"])
        m = compute_metrics(te["label"], pred, get_scores(pipe, te["clean"]))
        rows.append({"normalizer": name, "vocabulary_size": len(pipe["tfidf"].vocabulary_),
                     "accuracy": m["accuracy"], "f1": m["f1"],
                     "preprocess_seconds": round(prep_seconds, 2)})
        _log(f"  {name:<6} vocab={rows[-1]['vocabulary_size']:>6}  "
             f"acc={m['accuracy']:.4f}  f1={m['f1']:.4f}", verbose)
    return pd.DataFrame(rows)


def run_training(data=None, fake=None, real=None, normalizer="lemma", model_names=None,
                 fast=False, cv=None, sample=None, test_size=None,
                 compare_prep=False, output_dir=None, model_path=None, verbose=True):
    """Train, tune and evaluate models. Returns a dict summarising the run."""
    cv = cv or config.CV_FOLDS
    test_size = test_size or config.TEST_SIZE
    output_dir = Path(output_dir or config.REPORTS_DIR)
    model_path = Path(model_path or config.MODEL_PATH)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. data ---------------------------------------------------------------
    df = load_dataset(data, fake, real)
    source = df.attrs.get("source", "custom")
    if sample and sample < len(df):
        df = df.sample(n=sample, random_state=config.RANDOM_STATE).reset_index(drop=True)
    counts = df["label"].value_counts().to_dict()
    _log(f"Dataset: {len(df)} articles  (REAL={counts.get(0, 0)}, FAKE={counts.get(1, 0)})", verbose)
    if source == "sample":
        _log("WARNING: using the bundled SYNTHETIC sample data - metrics are not "
             "representative of real news. See README to use a real dataset.", verbose)

    # 2. split BEFORE preprocessing/vectorising so the test set stays untouched
    train_df, test_df = train_test_split(
        df, test_size=test_size, stratify=df["label"], random_state=config.RANDOM_STATE)

    # 3. preprocessing ------------------------------------------------------
    _log(f"Preprocessing ({normalizer}) using {backend_info()} ...", verbose)
    preprocessor = make_preprocessor(normalizer)
    train_p = _preprocess_frame(train_df, preprocessor)
    test_p = _preprocess_frame(test_df, preprocessor)
    X_train, y_train = train_p["clean"].tolist(), train_p["label"].to_numpy()
    X_test, y_test = test_p["clean"].tolist(), test_p["label"].to_numpy()
    _log(f"Train={len(X_train)}  Test={len(X_test)}", verbose)

    # 4. tune + evaluate each model ----------------------------------------
    cv_split = StratifiedKFold(n_splits=cv, shuffle=True, random_state=config.RANDOM_STATE)
    results, fitted, roc_data, reports = [], {}, {}, {}
    for spec in get_model_specs(model_names):
        grid = spec.fast_grid if fast else spec.param_grid
        size = len(ParameterGrid(grid))
        pipe = build_pipeline(spec.estimator)
        common = dict(scoring="f1", cv=cv_split, n_jobs=config.N_JOBS, refit=True)
        if spec.n_iter and size > spec.n_iter:
            search = RandomizedSearchCV(pipe, grid, n_iter=spec.n_iter,
                                        random_state=config.RANDOM_STATE, **common)
            how = f"randomized search ({spec.n_iter} of {size})"
        else:
            search = GridSearchCV(pipe, grid, **common)
            how = f"grid search ({size} combos)"
        _log(f"\n[{spec.label}] {how} x {cv}-fold CV ...", verbose)
        t0 = time.time()
        search.fit(X_train, y_train)
        seconds = time.time() - t0

        best = search.best_estimator_
        y_pred = best.predict(X_test)
        y_score = get_scores(best, X_test)
        m = compute_metrics(y_test, y_pred, y_score)
        from sklearn.metrics import classification_report
        reports[spec.name] = classification_report(
            y_test, y_pred, target_names=["REAL", "FAKE"], zero_division=0)
        fitted[spec.name] = best
        roc_data[spec.label] = (y_test, y_score)
        results.append({
            "model": spec.name, "label": spec.label,
            "best_params": str(search.best_params_),
            "cv_f1": float(search.best_score_),
            **{k: m[k] for k in ("accuracy", "precision", "recall", "f1", "roc_auc")},
            "confusion_matrix": m["confusion_matrix"],
            "train_seconds": round(seconds, 1),
        })
        _log(f"  best params : {search.best_params_}", verbose)
        _log(f"  CV F1={search.best_score_:.4f} | test acc={m['accuracy']:.4f} "
             f"prec={m['precision']:.4f} rec={m['recall']:.4f} f1={m['f1']:.4f} "
             f"auc={m['roc_auc']:.4f}  ({seconds:.1f}s)", verbose)
        plot_confusion_matrix(m["confusion_matrix"],
                              output_dir / f"confusion_matrix_{spec.name}.png", spec.label)

    # 5. choose best by CROSS-VALIDATION score (never by the test set) -------
    table = pd.DataFrame(results)
    best_row = table.loc[table["cv_f1"].idxmax()]  # ties -> first model in the list
    best_name = best_row["model"]
    _log(f"\nBest model (highest CV F1): {best_row['label']}", verbose)

    table.drop(columns=["confusion_matrix"]).to_csv(output_dir / "model_comparison.csv", index=False)
    plot_model_comparison(results, output_dir / "model_comparison.png")
    plot_roc_curves(roc_data, output_dir / "roc_curves.png")
    tf = top_features(fitted[best_name])
    if tf:
        plot_top_features(*tf, output_dir / f"top_features_{best_name}.png",
                          f"Most influential words - {best_row['label']}")
        pd.DataFrame(
            [{"direction": "FAKE", "word": w, "weight": v} for w, v in tf[0]] +
            [{"direction": "REAL", "word": w, "weight": v} for w, v in tf[1]]
        ).to_csv(output_dir / "top_features.csv", index=False)

    prep_table = None
    if compare_prep:
        _log("\nComparing preprocessing strategies (logistic regression baseline):", verbose)
        prep_table = compare_preprocessing(train_df, test_df, verbose)
        prep_table.to_csv(output_dir / "preprocessing_comparison.csv", index=False)

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "data_source": source, "n_articles": int(len(df)),
        "normalizer": normalizer, "nlp_backend": backend_info(),
        "fast_mode": fast, "cv_folds": cv, "best_model": best_name,
        "results": results, "classification_reports": reports,
    }
    (output_dir / "results.json").write_text(json.dumps(summary, indent=2, default=str))

    # 6. persist the best model + everything needed to reproduce preprocessing
    best_metrics = {k: float(best_row[k]) for k in
                    ("cv_f1", "accuracy", "precision", "recall", "f1", "roc_auc")}
    joblib.dump({
        "pipeline": fitted[best_name],
        "preprocessor_config": preprocessor.config(),
        "model_name": best_row["label"],
        "metrics": best_metrics,
        "trained_on_sample_data": source == "sample",
        "created_at": summary["created_at"],
    }, model_path)
    _log(f"Saved model   -> {model_path}", verbose)
    _log(f"Saved reports -> {output_dir}", verbose)
    return {"summary": summary, "table": table, "preprocessing_table": prep_table,
            "model_path": model_path, "output_dir": output_dir}
