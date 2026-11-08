"""
Inject realistic "messy applicant" noise and missing values into the clean
household dataset, so a model can be trained on data that looks like what
real users actually submit.

    from add_noise import add_noise
    noisy, report = add_noise(clean_df, level=1.0, seed=0)

Corruptions applied (each independently, scaled by `level`):
  * Rounding        - users report "about $1,500" instead of $1,487
  * Jitter          - small multiplicative error on money fields
  * Typos           - transposed digit, extra zero, dropped digit
  * Annual entry    - income typed as yearly instead of monthly (x12)
  * Earned == gross - users who don't separate earned from unearned income
  * Count noise     - household_size off by 1, applicant_age off by a few years
  * Boolean flips   - misunderstood yes/no questions
  * Nulls           - per-column missingness, plus "low-effort" rows that skip
                      many questions at once (correlated missingness)
Nulls are applied last, so a null always wins over a noisy value.

The input frame is never modified. Output dtypes are nullable
(float64 / Int64 / boolean), so pd.NA is preserved and CSV round-trips cleanly.
"""
import numpy as np
import pandas as pd

MONEY = ["gross_monthly_income", "earned_monthly_income",
         "rent_monthly", "utilities_monthly"]
COUNTS = ["household_size", "applicant_age"]
BOOLS = ["has_elderly_member", "has_disabled_member", "has_pregnant_member",
         "has_child_under_5", "receives_snap", "receives_medicaid",
         "receives_tanf", "receives_lachip", "receives_lamoms", "has_medicare",
         "has_other_health_insurance", "is_louisiana_resident"]

# Baseline per-column probability of a missing value (before row-level effects).
DEFAULT_NULL_RATES = {
    "household_size": 0.005, "applicant_age": 0.01,
    "gross_monthly_income": 0.04, "earned_monthly_income": 0.06,
    "rent_monthly": 0.08, "utilities_monthly": 0.10,
    "has_elderly_member": 0.01, "has_disabled_member": 0.03,
    "has_pregnant_member": 0.03, "has_child_under_5": 0.01,
    "receives_snap": 0.02, "receives_medicaid": 0.03, "receives_tanf": 0.04,
    "receives_lachip": 0.05, "receives_lamoms": 0.05, "has_medicare": 0.03,
    "has_other_health_insurance": 0.04, "is_louisiana_resident": 0.01,
}


def _typo(x, rng):
    """Corrupt one number: transpose adjacent digits, append a 0, or drop a digit."""
    s = str(int(round(x)))
    kind = int(rng.integers(3))
    if kind == 0 and len(s) >= 2:
        i = int(rng.integers(len(s) - 1))
        s = s[:i] + s[i + 1] + s[i] + s[i + 2:]
    elif kind == 1:
        s += "0"
    else:
        s = s[:-1] or "0"
    return float(s)


def add_noise(
    df,
    level=1.0,                 # global multiplier on every rate below (0 = no-op)
    seed=None,
    null_rates=None,           # dict overriding DEFAULT_NULL_RATES per column
    row_abandon_rate=0.04,     # share of "low-effort" rows that skip many fields
    abandon_multiplier=6.0,    # null-rate boost for those rows
    rounding_rate=0.25,
    jitter_rate=0.15,
    jitter_sd=0.05,
    typo_rate=0.01,
    annual_entry_rate=0.01,
    earned_equals_gross_rate=0.03,
    count_noise_rate=0.04,
    bool_flip_rate=0.02,
):
    """Return (noisy_df, report). `report` lists, per column, the fraction of
    values that became null and the fraction that were altered but not null."""
    rng = np.random.default_rng(seed)
    n = len(df)
    p = lambda x: min(max(x * level, 0.0), 1.0)
    hit = lambda rate: rng.random(n) < p(rate)

    out = df.copy()
    for c in MONEY:
        out[c] = out[c].astype("float64")
    for c in COUNTS:
        out[c] = out[c].astype("float64")

    # ---- row-level money behaviour -----------------------------------------
    lump = hit(earned_equals_gross_rate) & (out["earned_monthly_income"] > 0)
    out.loc[lump, "earned_monthly_income"] = out.loc[lump, "gross_monthly_income"]

    annual = hit(annual_entry_rate)                    # same row: both incomes x12
    for c in ("gross_monthly_income", "earned_monthly_income"):
        out.loc[annual, c] = out.loc[annual, c] * 12

    # ---- per-column money noise --------------------------------------------
    for c in MONEY:
        v = out[c].to_numpy(copy=True)
        m = hit(jitter_rate)
        v[m] *= rng.normal(1.0, jitter_sd, m.sum())
        m = hit(rounding_rate)
        base = 100 if "income" in c else 50
        v[m] = np.round(v[m] / base) * base
        for i in np.flatnonzero(hit(typo_rate) & (v > 0)):
            v[i] = _typo(v[i], rng)
        out[c] = np.round(np.clip(v, 0, None))

    # ---- counts ------------------------------------------------------------
    v = out["household_size"].to_numpy(copy=True)
    m = hit(count_noise_rate)
    v[m] = np.clip(v[m] + rng.choice([-1, 1], m.sum()), 1, None)
    out["household_size"] = v

    v = out["applicant_age"].to_numpy(copy=True)
    m = hit(count_noise_rate * 1.25)
    v[m] = np.clip(v[m] + rng.integers(-3, 4, m.sum()), 0, 110)
    out["applicant_age"] = v

    # ---- boolean flips -----------------------------------------------------
    for c in BOOLS:
        flip = hit(bool_flip_rate)
        out[c] = out[c].astype(bool) ^ flip

    # ---- nulls (last, so they override noise) ------------------------------
    rates = {**DEFAULT_NULL_RATES, **(null_rates or {})}
    abandon = hit(row_abandon_rate)
    nulled = pd.DataFrame(False, index=out.index, columns=df.columns)
    for c in df.columns:
        r = p(rates.get(c, 0.03))
        per_row = np.where(abandon, min(r * abandon_multiplier, 1.0), r)
        nulled[c] = rng.random(n) < per_row

    out[COUNTS] = out[COUNTS].astype("Int64")
    out[BOOLS] = out[BOOLS].astype("boolean")
    for c in df.columns:
        out[c] = out[c].mask(nulled[c])

    # ---- report ------------------------------------------------------------
    rows = []
    for c in df.columns:
        a = df[c].reset_index(drop=True)
        b = out[c].reset_index(drop=True)
        altered = b.notna() & (b.astype("float64") != a.astype("float64"))
        rows.append({"column": c,
                     "null_frac": round(float(b.isna().mean()), 4),
                     "altered_frac": round(float(altered.mean()), 4)})
    return out, pd.DataFrame(rows).set_index("column")


if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "la_households_synthetic.csv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "la_households_noisy.csv"
    clean = pd.read_csv(src)
    noisy, report = add_noise(clean, level=1.0, seed=0)
    noisy.to_csv(dst, index=False)
    print(report.to_string())
    print(f"\nrows with >=1 null: {noisy.isna().any(axis=1).mean():.1%}")
    print(f"rows with >=5 nulls: {(noisy.isna().sum(axis=1) >= 5).mean():.1%}")