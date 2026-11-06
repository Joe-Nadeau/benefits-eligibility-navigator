from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder


NUMERIC_FEATURES = [
    "household_size",
    "gross_monthly_income",
]

BOOLEAN_FEATURES = [
    "receives_snap",
    "receives_medicaid",
    "receives_tanf",
    "receives_lachip",
    "receives_lamoms",
    "is_louisiana_resident",
]


def create_wic_preprocessor():
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("boolean", "passthrough", BOOLEAN_FEATURES),
        ]
    )