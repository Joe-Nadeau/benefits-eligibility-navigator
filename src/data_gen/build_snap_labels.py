"""
Generate SNAP labels for a household data file and write them to their own CSV.
The data file is never modified or merged with the labels.

CLI:
  python generate_labels.py <clean_data.csv> [labels.csv] [--bbce] [--reasons]

Output columns: household_id, snap_eligible [, snap_reason]
  household_id = the file's own household_id column if it has one, otherwise
                 the 0-based row number (so the data file must keep its row order).

IMPORTANT: pass the CLEAN data file. Labels must reflect the true household,
not the corrupted version a noisy file contains. Row order and household_id are
shared with the noisy file, so the same labels line up with it.

Loading for training:
  from generate_labels import load_xy
  X, y = load_xy("la_households_noisy.csv", "labels.csv", FEATURES, "snap_eligible")
"""

import sys
import pandas as pd
from ..rules import derive_net_monthly_income, snap_eligibility

REQUIRED = ["household_size", "gross_monthly_income", "earned_monthly_income",
            "rent_monthly", "utilities_monthly",
            "has_elderly_member", "has_disabled_member"]


def generate_snap_labels(data, bbce=False, include_reasons=False):
    """Return a labels DataFrame for `data` (clean, null-free)."""
    missing_cols = [c for c in REQUIRED if c not in data.columns]
    if missing_cols:
        raise ValueError(f"data is missing columns: {missing_cols}")
    if data[REQUIRED].isna().any().any():
        raise ValueError("data has nulls in rule inputs; label from the CLEAN "
                         "file (snap_eligibility would treat NaN income as eligible)")

    df = data.copy()
    df["net_monthly_income"] = derive_net_monthly_income(df)   # used only to label
    results = df.apply(lambda row: snap_eligibility(row, bbce=bbce), axis=1)

    ids = data["household_id"] if "household_id" in data.columns \
        else pd.Series(range(len(data)), index=data.index)
    labels = pd.DataFrame({
        "household_id": ids.to_numpy(),
        "snap_eligible": results.map(lambda r: r["eligible"]).astype(bool).to_numpy(),
    })
    if include_reasons:
        labels["snap_reason"] = results.map(lambda r: r["reason"]).to_numpy()
    return labels


def load_xy(features_csv, labels_csv, feature_cols, label_col="snap_eligible"):
    """Join a data file and a labels file on household_id (or row number)."""
    X = pd.read_csv(features_csv)
    y = pd.read_csv(labels_csv)
    if "household_id" in X.columns:
        merged = X.merge(y[["household_id", label_col]], on="household_id", how="inner")
    else:
        assert len(X) == len(y), "row counts differ and no household_id to join on"
        merged = X.assign(**{label_col: y[label_col].to_numpy()})
    return merged[feature_cols], merged[label_col]


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    data_path = args[0] if args else "data/la_households_synthetic.csv"
    out_path = args[1] if len(args) > 1 else "data/labels/snap_labels.csv"
    labels = generate_snap_labels(pd.read_csv(data_path),
                                  bbce="--bbce" in sys.argv,
                                  include_reasons="--reasons" in sys.argv)
    labels.to_csv(out_path, index=False)
    print(f"wrote {len(labels)} labels to {out_path} "
          f"(eligible: {labels.snap_eligible.mean():.1%})")