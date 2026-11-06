def medicaid_eligibility(features):
    size = features["household_size"]
    income = features["gross_monthly_income"]
    age = features["applicant_age"]

    # Louisiana Medicaid monthly income limits, effective 3/1/2026.
    limits = {
        "expansion": [
            1836, 2489, 3142, 3795,
            4449, 5102, 5755, 6408
        ],
        "lachip": [
            2887, 3914, 4941, 5968,
            6995, 8022, 9049, 10077
        ],
        "lachip_affordable": [
            3392, 4599, 5806, 7013,
            8220, 9427, 10634, 11841
        ],
        "lamoms": [
            None, 2489, 3142, 3795,
            4449, 5102, 5755, 6408
        ],
        "family_opportunity": [
            3990, 5410, 6830, 8250,
            9670, 11090, 12510, 13930
        ]
    }

    def get_limit(program):
        program_limits = limits[program]

        if size <= 8:
            return program_limits[size - 1]

        return program_limits[7] + (size - 8) * (
            program_limits[7] - program_limits[6]
        )

    # Check Medicaid Expansion.
    if (
        19 <= age <= 64
        and not features["has_medicare"]
        and income <= get_limit("expansion")
    ):
        return {
            "eligible": True,
            "program": "Medicaid Expansion",
            "reason": "Applicant passes the Expansion income and age tests."
        }

    # Check LaCHIP for children.
    if (
        age < 19
        and not features.get("has_other_health_insurance", False)
        and income <= get_limit("lachip")
    ):
        return {
            "eligible": True,
            "program": "LaCHIP",
            "reason": "Child passes the LaCHIP income and insurance tests."
        }

    # Check LaCHIP Affordable Plan.
    if (
        age < 19
        and features.get("has_other_health_insurance", False)
        and income <= get_limit("lachip_affordable")
    ):
        return {
            "eligible": True,
            "program": "LaCHIP Affordable Plan",
            "reason": "Child passes the Affordable Plan income check."
        }

    # Check LaMOMS.
    if (
        features["has_pregnant_member"]
        and income <= get_limit("lamoms")
    ):
        return {
            "eligible": True,
            "program": "LaMOMS",
            "reason": "Applicant passes the LaMOMS income check."
        }

    # Check Family Opportunity Act.
    if (
        age < 19
        and features["has_disabled_member"]
        and income <= get_limit("family_opportunity")
    ):
        return {
            "eligible": True,
            "program": "Family Opportunity Act",
            "reason": "Applicant passes the Family Opportunity Act income check."
        }

    return {
        "eligible": False,
        "program": None,
        "reason": "Applicant did not pass any implemented Medicaid category."
    }