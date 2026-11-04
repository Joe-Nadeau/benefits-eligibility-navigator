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
    "applicant_category",
    "nutritional_risk",
    "is_louisiana_resident",
]

MEDICAID_FEATURES = [
    "household_size",
    "gross_monthly_income",
    "applicant_age",
    "applicant_category",
    "has_medicare",
    "has_other_health_insurance",
    "has_pregnant_member",
    "has_disabled_member",
]


def extract_features(data, feature_list):
    return {
        feature: data[feature]
        for feature in feature_list
    }


def extract_snap_features(data):
    return extract_features(data, SNAP_FEATURES)


def extract_wic_features(data):
    return extract_features(data, WIC_FEATURES)


def extract_medicaid_features(data):
    return extract_features(data, MEDICAID_FEATURES)