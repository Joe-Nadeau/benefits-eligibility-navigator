from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


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