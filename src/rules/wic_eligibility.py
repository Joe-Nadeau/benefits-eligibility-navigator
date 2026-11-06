def wic_eligibility(features):
    size = features["household_size"]
    gross = features["gross_monthly_income"]

    # Louisiana WIC 2026-2027 monthly income limits.
    limits = {
        1: 2461, 2: 3337, 3: 4212, 4: 5088,
        5: 5964, 6: 6839, 7: 7715, 8: 8591,
        9: 9466, 10: 10342, 11: 11218, 12: 12093,
        13: 12969, 14: 13845, 15: 14720, 16: 15596
    }

    # Count unborn fetus as an additional household member.
    if features["has_pregnant_member"]:
        size += 1

    size_for_limit = min(size, 16)
    income_limit = limits[size_for_limit]

    if size > 16:
        income_limit += (size - 16) * 876

    # Qualifying program enrollment establishes income eligibility.
    adjunctively_eligible = any([
        features.get("receives_snap", False),
        features.get("receives_medicaid", False),
        features.get("receives_tanf", False),
        features.get("receives_lachip", False),
        features.get("receives_lamoms", False)
    ])

    # Applicant must belong to a WIC category.
    category_eligible = (
        features["has_pregnant_member"]
        or features.get("applicant_category") in [
            "infant",
            "child",
            "postpartum",
            "breastfeeding"
        ]
    )

    if not category_eligible:
        return {
            "eligible": False,
            "reason": "Applicant does not meet a WIC participant category."
        }

    if not adjunctively_eligible and gross > income_limit:
        return {
            "eligible": False,
            "reason": "Gross income exceeds the WIC income limit."
        }

    if not features.get("nutritional_risk", False):
        return {
            "eligible": False,
            "reason": "Nutritional risk requirement is not met."
        }

    if not features.get("is_louisiana_resident", True):
        return {
            "eligible": False,
            "reason": "Applicant does not meet Louisiana residency requirements."
        }

    return {
        "eligible": True,
        "reason": (
            "Applicant passes the simplified WIC category, "
            "income, and nutritional-risk checks."
        )
    }