"""Single source of truth for the household input fields."""

# TODO (team meeting): decide whether net_monthly_income is a user-provided
# input or a value derived by the rules module.
FEATURES = [
    "household_size",
    "adults",
    "children",
    "gross_monthly_income",
    "earned_monthly_income",
    "unearned_monthly_income",
    "net_monthly_income",
    "rent_monthly",
    "utilities_monthly",
    "has_elderly_member",
    "has_disabled_member",
    "has_pregnant_member",
]