"""Single source of truth for the household input fields."""

# TODO (team meeting): decide whether net_monthly_income is a user-provided
# input or a value derived by the rules module.
FEATURES = [
    # Total number of people in the household.
    # Example: 3
    "household_size",

    # Total household gross monthly income before deductions (includes unearned and earned income).
    # Example: 3500.00
    "gross_monthly_income",

    # Total household net monthly income after applicable deductions.
    # Will be derived from 
    # Example: 2800.00
    # "net_monthly_income", 
    
    # Total household earned monthly income from active work or services performed.
    # Example: 3000.00
    "earned_monthly_income",

    # Total rent paid monthly.
    # Example: 200.00
    "rent_monthly",

    # Total utilies paid monthly.
    # Example: 100.00
    "utilities_monthly",

    # Whether any household member is age 60 or older.
    # Example: True
    "has_elderly_member",

    # Whether any household member has a qualifying disability.
    # Example: True
    "has_disabled_member",

    # Whether any household member is currently pregnant.
    # Example: True
    "has_pregnant_member",

    # Whether any household member is under 5.
    # Example: True
    "has_child_under_5",

    # Whether the household currently receives SNAP benefits.
    # Example: True
    "receives_snap",

    # Whether the household currently receives Medicaid.
    # Example: False
    "receives_medicaid",

    # Whether the household currently receives Temporary Assistance
    # for Needy Families (TANF).
    # Example: False
    "receives_tanf",

    # Whether the household currently receives Louisiana Children's
    # Health Insurance Program (LaCHIP) benefits.
    # Example: True
    "receives_lachip",

    # Whether the household currently receives Louisiana Medicaid
    # coverage through the LaMOMS program.
    # Example: False
    "receives_lamoms",

    # Age of the individual applying for benefits.
    # Example: 28
    "applicant_age",

    # Whether the applicant is currently enrolled in Medicare.
    # Example: False
    "has_medicare",

    # Whether the applicant currently has other health insurance.
    # Example: True
    "has_other_health_insurance",

    # Whether the applicant lives in Louisiana.
    # Example: True
    "is_louisiana_resident",
]

