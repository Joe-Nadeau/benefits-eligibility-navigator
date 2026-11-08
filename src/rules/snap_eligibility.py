"""SNAP rules: net-income derivation + your snap_eligibility() (unchanged)."""
import numpy as np
import pandas as pd

# FY 2027 (Oct 1 2026 - Sep 30 2027), 48 states + DC.
STANDARD_DEDUCTION = {"1-3": 217, "4": 229, "5": 268, "6+": 308}
SHELTER_CAP = 769          # does not apply to elderly/disabled households
EARNED_INCOME_DEDUCTION = 0.20


def _flag(s):
    """Missing / NA booleans count as False."""
    return s.eq(True).fillna(False).astype(bool)


def derive_net_monthly_income(df):
    """Vectorized net income per 7 CFR 273.9, using only columns we have.

    Steps: gross - 20% of earned - standard deduction, then subtract the excess
    shelter deduction (rent + utilities above half of the remaining income;
    capped at $769 unless a member is elderly/disabled). Floors at 0.

    NOT modeled (no columns for them): dependent care, legally owed child
    support, excess medical (elderly/disabled, > $35), and Louisiana's standard
    utility allowance (actual utilities are used instead).

    Missing-data convention (matters for the noisy data): missing gross income
    or household size -> NaN net income; missing earned income, rent, or
    utilities -> treated as 0 (the deduction simply isn't claimed); missing
    elderly/disabled flags -> False.
    """
    size = df["household_size"].astype("float64")
    gross = df["gross_monthly_income"].astype("float64")
    earned = df["earned_monthly_income"].astype("float64").fillna(0.0)
    earned = np.minimum(earned, gross)           # earned can't exceed gross
    shelter = (df["rent_monthly"].astype("float64").fillna(0.0)
               + df["utilities_monthly"].astype("float64").fillna(0.0))
    uncapped = _flag(df["has_elderly_member"]) | _flag(df["has_disabled_member"])

    std = np.select([size <= 3, size == 4, size == 5],
                    [STANDARD_DEDUCTION["1-3"], STANDARD_DEDUCTION["4"],
                     STANDARD_DEDUCTION["5"]],
                    default=STANDARD_DEDUCTION["6+"])
    after = np.maximum(0.0, gross - EARNED_INCOME_DEDUCTION * earned - std)
    excess = np.maximum(0.0, shelter - 0.5 * after)
    excess = np.where(uncapped, excess, np.minimum(excess, SHELTER_CAP))
    net = np.maximum(0.0, after - excess)
    return pd.Series(np.round(net), index=df.index, name="net_monthly_income")


def snap_eligibility(features, bbce=False):
    size = features["household_size"]
    gross = features["gross_monthly_income"]
    net = features["net_monthly_income"]

    # FY 2027 limits for the 48 contiguous states.
    gross_limits = {
        1: 1729, 2: 2345, 3: 2960, 4: 3575,
        5: 4191, 6: 4806, 7: 5421, 8: 6037
    }

    net_limits = {
        1: 1330, 2: 1804, 3: 2277, 4: 2750,
        5: 3224, 6: 3697, 7: 4170, 8: 4644
    }

    extra = max(0, size - 8)
    base_size = min(size, 8)

    gross_limit = gross_limits[base_size] + extra * 616
    net_limit = net_limits[base_size] + extra * 474

    # Louisiana BBCE gross limit is 200% of the poverty level.
    if bbce:
        gross_limit = round(gross_limit * 200 / 130)

    elderly_or_disabled = (
        features["has_elderly_member"]
        or features["has_disabled_member"]
    )

    # Elderly/disabled households are exempt from the
    # regular gross-income test.
    if not elderly_or_disabled and gross > gross_limit:
        return {
            "eligible": False,
            "reason": "Gross income exceeds the SNAP limit."
        }

    if net > net_limit:
        return {
            "eligible": False,
            "reason": "Net income exceeds the SNAP limit."
        }

    return {
        "eligible": True,
        "reason": "Household passes the simplified SNAP income tests."
    }