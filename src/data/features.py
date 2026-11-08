SNAP_FEATURES = [
    "household_size",
    "gross_monthly_income",
    "net_monthly_income",
    "has_elderly_member",
    "has_disabled_member",
]

WIC_FEATURES = [
    "household_size",
    "gross_monthly_income",
    "receives_snap",
    "receives_medicaid",
    "receives_tanf",
    "receives_lachip",
    "receives_lamoms",
    "has_pregnant_member",
    "has_child_under_5",
    "is_louisiana_resident",
]

MEDICAID_FEATURES = [
    "household_size",
    "gross_monthly_income",
    "applicant_age",
    "has_medicare",
    "has_other_health_insurance",
    "has_pregnant_member",
    "has_disabled_member",
]


def extract_features(data, feature_list):
    return {
        feature: data.get(feature)
        for feature in feature_list
    }


def extract_snap_features(data):
    snap_data = data.copy()

    # Calculate SNAP-specific net income.
    snap_data["net_monthly_income"] = calculate_snap_net_income(data)

    return {
        feature: snap_data.get(feature)
        for feature in SNAP_FEATURES
    }


def extract_wic_features(data):
    return extract_features(data, WIC_FEATURES)


def extract_medicaid_features(data):
    return extract_features(data, MEDICAID_FEATURES)

def calculate_snap_net_income(data):
    gross_income = data["gross_monthly_income"]
    earned_income = data["earned_monthly_income"]

    # Calculate applicable SNAP deductions here.
    earned_deduction = earned_income * 0.20

    # TODO: Add standard deduction, dependent care,
    # child support, medical, and shelter deductions.

    net_income = gross_income - earned_deduction

    return max(0, net_income)