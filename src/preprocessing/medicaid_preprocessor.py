from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder


NUMERIC_FEATURES = [
    "household_size",
    "gross_monthly_income",
    "applicant_age",
]

BOOLEAN_FEATURES = [
    "has_medicare",
    "has_other_health_insurance",
    "has_pregnant_member",
    "has_disabled_member",
]


def create_medicaid_preprocessor():
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("boolean", "passthrough", BOOLEAN_FEATURES),
        ]
    )