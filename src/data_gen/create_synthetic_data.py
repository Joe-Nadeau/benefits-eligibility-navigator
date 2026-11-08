"""
Synthetic Louisiana household dataset generator for benefits-eligibility models.

Produces N households with the columns in FEATURES (net_monthly_income is
intentionally excluded -- it is derived by the rules module).

Approach: build each household bottom-up (size -> composition -> ages ->
disability/pregnancy -> income -> program participation -> housing costs) so
that the fields are internally consistent, rather than sampling each column
independently. Targets are approximate ACS / CMS / LDH-style figures written
from memory; they are NOT pulled from live data. For production-grade
representativeness, re-calibrate against ACS PUMS for Louisiana.

Usage:  python generate_la_households.py [N] [SEED] [OUTPUT_CSV]
"""
import sys
import numpy as np
import pandas as pd

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 42
OUT = sys.argv[3] if len(sys.argv) > 3 else "la_households_synthetic.csv"
rng = np.random.default_rng(SEED)

FEATURES = [
    "household_size", "gross_monthly_income", "earned_monthly_income",
    "rent_monthly", "utilities_monthly", "has_elderly_member",
    "has_disabled_member", "has_pregnant_member", "has_child_under_5",
    "receives_snap", "receives_medicaid", "receives_tanf", "receives_lachip",
    "receives_lamoms", "applicant_age", "has_medicare",
    "has_other_health_insurance", "is_louisiana_resident",
]

# ---- assumptions -----------------------------------------------------------
SIZES = [1, 2, 3, 4, 5, 6, 7]
SIZE_P = [0.285, 0.32, 0.17, 0.12, 0.065, 0.025, 0.015]   # avg ~2.6 persons
P_KIDS = {1: 0, 2: 0.12, 3: 0.55, 4: 0.75, 5: 0.88, 6: 0.92, 7: 0.93}
P_RESIDENT = 0.97                    # small share of non-residents as negatives


def fpl_monthly(n):
    """2025 HHS poverty guideline (48 states), monthly."""
    return (15650 + 5500 * (n - 1)) / 12


def lognorm(median, sigma):
    return float(rng.lognormal(np.log(median), sigma))


def pick(table, r):
    """table = [(upper_bound_ratio, prob), ...] ascending; last bound = inf."""
    for bound, p in table:
        if r < bound:
            return p
    return table[-1][1]


def bern(p):
    return bool(rng.random() < min(max(p, 0.0), 1.0))


def household():
    n = int(rng.choice(SIZES, p=SIZE_P))

    # --- composition
    k = 0
    if n >= 2 and bern(P_KIDS[n]):
        k = 1 if n == 2 else 1 + int(rng.binomial(n - 2, 0.55))
        k = min(k, n - 1)
        if n >= 4 and bern(0.8):
            k = min(k, n - 2)
    adults = n - k
    u5 = int(rng.binomial(k, 0.28)) if k else 0

    # --- elderly (60+)
    p_eld = 0.12 if k else {1: 0.42, 2: 0.50}.get(n, 0.25)
    elderly = bern(p_eld)
    e = 0
    if elderly:
        e = 2 if (adults >= 2 and bern(0.10 if k else 0.50)) else 1
        e = min(e, adults)
    wa = adults - e                              # working-age adults

    # --- applicant age
    app_elderly = elderly and (wa == 0 or bern(0.25 if k else 0.55))
    if app_elderly:
        age = int(np.clip(60 + rng.gamma(2, 6.0), 60, 98))
    elif k:
        age = int(np.clip(round(rng.normal(34, 8)), 18, 59))
    else:
        age = int(np.clip(round(rng.normal(41, 13)), 18, 59))

    # --- disability
    p_dis = (0.33 if elderly else 0.11) * (1 + 0.15 * (adults - 1))
    disabled = bern(p_dis)

    # --- pregnancy
    if wa >= 1:
        if u5:
            p_preg = 0.07
        elif k:
            p_preg = 0.025
        elif n >= 2:
            p_preg = 0.025
        else:
            p_preg = 0.015 if age <= 44 else 0.0
    else:
        p_preg = 0.0
    pregnant = bern(p_preg)

    # --- earned income
    earned = 0.0
    for i in range(wa):
        if disabled and i == 0:
            p_work = 0.28
        elif adults == 1 and k:
            p_work = 0.58 if u5 else 0.70
        else:
            p_work = 0.82
        if bern(p_work):
            amt = lognorm(4300, 0.70)
            if bern(0.18):
                amt *= 0.45                      # part-time
            earned += float(np.clip(amt, 150, 25000))
    for _ in range(e):
        if bern(0.14):
            earned += float(np.clip(lognorm(1800, 0.7), 100, 8000))

    # --- unearned income (SS, pensions, SSI/SSDI, child support, etc.)
    unearned = 0.0
    for _ in range(e):
        if bern(0.92):
            unearned += lognorm(1650, 0.35)
        else:
            unearned += lognorm(600, 0.3) if bern(0.08) else 0.0
        if bern(0.20):
            unearned += lognorm(1100, 0.6)
    if disabled and bern(0.30 if elderly else 0.62):
        unearned += lognorm(1050, 0.38)
    if bern(0.22 if (k and adults == 1) else 0.07):
        unearned += float(np.clip(lognorm(450, 0.7), 30, 3000))

    if earned + unearned == 0 and bern(0.65):    # UI, gifts, SSI pending, etc.
        unearned += lognorm(700, 0.6)

    gross = earned + unearned
    r = gross / fpl_monthly(n)

    # --- TANF (decided on pre-TANF income; cash grant is unearned income)
    p_tanf = 0.0
    if k:
        p_tanf = 0.08 if r < 0.5 else (0.02 if r < 1.0 else 0.0)
    tanf = bern(p_tanf)
    if tanf:
        unearned += float(rng.uniform(180, 320))
        gross = earned + unearned
        r = gross / fpl_monthly(n)

    # --- SNAP
    if tanf:
        p_snap = 0.85
    else:
        p_snap = pick([(0.5, 0.45), (1.0, 0.62), (1.3, 0.50), (1.65, 0.26),
                       (2.0, 0.10), (np.inf, 0.02)], r)
        if k:
            p_snap *= 1.15
        if disabled:
            p_snap *= 1.10
        if elderly and wa == 0 and not k:
            p_snap *= 0.70                       # low take-up among seniors
    snap = bern(min(p_snap, 0.92))

    # --- LA-specific child / pregnancy programs
    resident = bern(P_RESIDENT)
    lachip = False
    if resident and k:
        lachip = bern(pick([(1.42, 0.05), (2.12, 0.62), (2.55, 0.12),
                            (np.inf, 0.0)], r))
    lamoms = False
    if resident and pregnant:
        lamoms = bern(pick([(1.38, 0.68), (2.14, 0.22), (np.inf, 0.02)], r))

    # --- Medicaid
    p_med = pick([(1.38, 0.82), (2.0, 0.34), (3.0, 0.14), (np.inf, 0.04)], r)
    if k and r < 1.47:
        p_med = 0.85
    if elderly:
        p_med = max(p_med, 0.60 if r < 1.0 else (0.20 if r < 2.0 else p_med))
    if disabled:
        p_med *= 1.2
    if lachip or lamoms:
        p_med *= 0.35
    medicaid = bern(min(p_med, 0.92))

    # --- Medicare / other insurance (applicant-level)
    if age >= 65:
        p_mc = 0.95
    elif age >= 60:
        p_mc = 0.04
    else:
        p_mc = 0.05 if disabled else 0.0
    medicare = bern(p_mc)

    if medicare:
        p_oi = 0.45
    elif medicaid or lachip or lamoms:
        p_oi = 0.12
    else:
        p_oi = pick([(1, 0.12), (1500, 0.25), (3000, 0.48), (5000, 0.72),
                     (np.inf, 0.88)], earned)
    other_ins = bern(p_oi)

    # --- housing costs
    p_rent = pick([(1.0, 0.70), (2.0, 0.52), (4.0, 0.32), (np.inf, 0.15)], r)
    if wa == 0:
        p_rent *= 0.6
    if n >= 4:
        p_rent *= 0.85
    renter = bern(p_rent)
    rent = 0.0
    if renter:
        if r < 1.0 and bern(0.18):               # subsidized: ~30% of income
            rent = max(50.0, 0.30 * gross)
        else:
            rent = float(np.clip(
                lognorm(480 + 0.09 * gross + 55 * (n - 1), 0.28), 250, 3200))
    util = lognorm(135 + 22 * (n - 1), 0.35) * (1.15 if not renter else 1.0)
    if r < 1.0:
        util *= 0.85
    util = float(np.clip(util, 30, 700))
    if renter and bern(0.06):
        util = 0.0                               # utilities included in rent

    return {
        "household_size": n,
        "gross_monthly_income": round(gross),
        "earned_monthly_income": round(earned),
        "rent_monthly": round(rent),
        "utilities_monthly": round(util),
        "has_elderly_member": elderly,
        "has_disabled_member": disabled,
        "has_pregnant_member": pregnant,
        "has_child_under_5": u5 > 0,
        "receives_snap": snap,
        "receives_medicaid": medicaid,
        "receives_tanf": tanf,
        "receives_lachip": lachip,
        "receives_lamoms": lamoms,
        "applicant_age": age,
        "has_medicare": medicare,
        "has_other_health_insurance": other_ins,
        "is_louisiana_resident": resident,
        "_kids": k,
    }


def main():
    rows = [household() for _ in range(N)]
    full = pd.DataFrame(rows)
    df = full[FEATURES].copy()

    # ---- consistency checks
    assert (df.earned_monthly_income <= df.gross_monthly_income).all()
    assert (full.loc[df.receives_lachip, "_kids"] > 0).all()
    assert df.loc[df.receives_lamoms, "has_pregnant_member"].all()
    assert df.loc[df.applicant_age >= 60, "has_elderly_member"].all()
    assert (df.loc[df.has_child_under_5, "household_size"] >= 2).all()

    df.to_csv(OUT, index=False)

    # ---- marginals for sanity-checking against known Louisiana figures
    fpl = df.household_size.map(fpl_monthly)
    ratio = df.gross_monthly_income / fpl
    print(f"rows={len(df)}  seed={SEED}")
    print(f"mean household size      : {df.household_size.mean():.2f}")
    print(f"median annual income     : ${df.gross_monthly_income.median()*12:,.0f}")
    print(f"mean annual income       : ${df.gross_monthly_income.mean()*12:,.0f}")
    print(f"zero-income households   : {(df.gross_monthly_income==0).mean():.1%}")
    print(f"below 100% FPL           : {(ratio<1).mean():.1%}")
    print(f"below 200% FPL           : {(ratio<2).mean():.1%}")
    print(f"renters                  : {(df.rent_monthly>0).mean():.1%}")
    print(f"median rent (renters)    : ${df.loc[df.rent_monthly>0,'rent_monthly'].median():,.0f}")
    print(f"median utilities         : ${df.utilities_monthly.median():,.0f}")
    print(df.select_dtypes(bool).mean().mul(100).round(1).to_string())
    print(df.household_size.value_counts(normalize=True).sort_index().round(3).to_string())


if __name__ == "__main__":
    main()

    # Usage: python generate_la_households.py 5000 7 out.csv