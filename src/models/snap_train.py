"""
Train a SNAP-eligibility classifier from a data file + a separate labels file.

  python train_snap_model.py [noisy.csv] [labels.csv] [clean.csv]

Flow:
  1. load noisy features, derive net_monthly_income FROM THE NOISY INPUTS
  2. join labels (household_id if present, else row order)
  3. hold out a stratified test set
  4. cross-validate a few models on the training portion, pick best by F1
  5. fit on all training data, report held-out metrics (noisy and clean features)
  6. save the fitted pipeline (preprocessing + model) to snap_model.joblib
"""
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, FunctionTransformer

from ..rules import derive_net_monthly_income

NUMERIC_FEATURES = ["household_size", "gross_monthly_income", "net_monthly_income"]
BOOLEAN_FEATURES = ["has_elderly_member", "has_disabled_member"]
SNAP_FEATURES = NUMERIC_FEATURES + BOOLEAN_FEATURES
LABEL = "snap_eligible"
SEED = 0


def makefloat64(num):
    return num.astype("float64")

to_float = FunctionTransformer(makefloat64)

def create_snap_preprocessor():
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scaler", StandardScaler()),
    ])
    boolean = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent", add_indicator=True)),
    ])
    return ColumnTransformer([
        ("numeric", numeric, NUMERIC_FEATURES),
        ("boolean", boolean, BOOLEAN_FEATURES),
    ])

def create_snap_preprocessor_null():
    """Create a preprocessor that allows nulls to pass through"""
    return ColumnTransformer([
        ("num", "passthrough", NUMERIC_FEATURES),
        ("bool", to_float, BOOLEAN_FEATURES),   # True/False/NaN -> 1.0/0.0/NaN
    ])


def load_features(path):
    """Read a household file and add the derived net income column."""
    df = pd.read_csv(path)
    df["net_monthly_income"] = derive_net_monthly_income(df)
    return df


def attach_labels(features, labels):
    if "household_id" in features.columns:
        return features.merge(labels[["household_id", LABEL]], on="household_id")
    assert len(features) == len(labels), "row counts differ and no household_id"
    return features.assign(**{LABEL: labels[LABEL].to_numpy()})


def candidate_models():
    return {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "random_forest": RandomForestClassifier(300, class_weight="balanced",
                                                random_state=SEED, n_jobs=-1),
        "hist_gradient_boosting": HistGradientBoostingClassifier(random_state=SEED),
        "hist_gradient_boosting_null": HistGradientBoostingClassifier(random_state=SEED),
    }


def make_pipeline(name, model):
    if name == 'hist_gradient_boosting_null':
        return Pipeline([("pre", create_snap_preprocessor_null()), ("model", model)])
    else: 
        return Pipeline([("preprocess", create_snap_preprocessor()), ("model", model)])


def predict_one(pipeline, household):
    """Score one raw household dict (needs the columns derive_net_monthly_income uses)."""
    row = pd.DataFrame([household])
    row["net_monthly_income"] = derive_net_monthly_income(row)
    p = float(pipeline.predict_proba(row[SNAP_FEATURES])[0, 1])
    return {"eligible": p >= 0.5, "probability": round(p, 3)}


def main():
    noisy_path = sys.argv[1] if len(sys.argv) > 1 else "data/la_households_noisy.csv"
    labels_path = sys.argv[2] if len(sys.argv) > 2 else "data/labels/snap_labels.csv"
    clean_path = sys.argv[3] if len(sys.argv) > 3 else "data/la_households_synthetic.csv"

    data = attach_labels(load_features(noisy_path), pd.read_csv(labels_path))
    clean = attach_labels(load_features(clean_path), pd.read_csv(labels_path))
    X, y = data[SNAP_FEATURES], data[LABEL].astype(bool)

    idx_train, idx_test = train_test_split(
        np.arange(len(data)), test_size=0.2, stratify=y, random_state=SEED)
    X_train, y_train = X.iloc[idx_train], y.iloc[idx_train]
    X_test, y_test = X.iloc[idx_test], y.iloc[idx_test]
    print(f"train={len(idx_train)} test={len(idx_test)} "
          f"eligible rate={y.mean():.1%}\n")

    # model selection via cross-validation on the training split only
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    best_name, best_f1 = None, -1
    for name, model in candidate_models().items():
        res = cross_validate(make_pipeline(name, model), X_train, y_train, cv=cv,
                             scoring=["accuracy", "precision", "recall", "f1"])
        f1 = res["test_f1"].mean()
        print(f"{name:24s} acc={res['test_accuracy'].mean():.3f} "
              f"prec={res['test_precision'].mean():.3f} "
              f"rec={res['test_recall'].mean():.3f} f1={f1:.3f}")
        if f1 > best_f1:
            best_name, best_f1 = name, f1
    print(f"\nselected: {best_name}\n")

    # final fit + held-out evaluation
    pipe = make_pipeline(best_name, candidate_models()[best_name]).fit(X_train, y_train)

    print("== held-out test, NOISY features (what real users submit) ==")
    pred = pipe.predict(X_test)
    print(classification_report(y_test, pred, target_names=["ineligible", "eligible"]))

    print("\n== same test households, CLEAN features (noise-free ceiling) ==")
    pred_c = pipe.predict(clean[SNAP_FEATURES].iloc[idx_test])
    print(f"accuracy={np.mean(pred_c == y_test):.3f}"
          f"(noisy: {np.mean(pred == y_test):.3f})")

    joblib.dump(pipe, "./src/models/snap_model.joblib")
    print("\nsaved snap_model.joblib")

    example = {"household_size": 3, "gross_monthly_income": 2400,
               "earned_monthly_income": 2400, "rent_monthly": 800,
               "utilities_monthly": 180, "has_elderly_member": False,
               "has_disabled_member": False}
    print("example prediction:", predict_one(pipe, example))


if __name__ == "__main__":
    main()