from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler


NUMERIC_FEATURES = [
    "household_size",
    "gross_monthly_income",
    "net_monthly_income",
]

BOOLEAN_FEATURES = [
    "has_elderly_member",
    "has_disabled_member",
]


def create_snap_preprocessor():
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("boolean", "passthrough", BOOLEAN_FEATURES),
        ]
    )