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