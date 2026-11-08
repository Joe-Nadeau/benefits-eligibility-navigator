from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


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
    "has_pregnant_member",
    "has_child_under_5",
    "is_louisiana_resident",
]


def create_wic_preprocessor():
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(
            strategy="median",
            add_indicator=True
        )),
        ("scaler", StandardScaler()),
    ])

    boolean_pipeline = Pipeline([
        ("imputer", SimpleImputer(
            strategy="most_frequent",
            add_indicator=True
        )),
    ])

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("boolean", boolean_pipeline, BOOLEAN_FEATURES),
        ]
    )