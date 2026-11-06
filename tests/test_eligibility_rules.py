import sys
from pathlib import Path

# 1. Get the path to the root folder (benefits-eligibility-navigator)
project_root = Path(__file__).resolve().parent.parent

# 2. Point specifically to the 'src' directory
src_path = str(project_root / "src")

# 3. Add 'src' to Python's search paths
if src_path not in sys.path:
    sys.path.append(src_path)

# Now Python can see 'rules' sitting inside 'src'
import rules

test_cases = [
    {
        "name": "Low-income family with children",
        "features": {
            "household_size": 4,
            "gross_monthly_income": 2500.00,
            "net_monthly_income": 2100.00,
            "has_elderly_member": False,
            "has_disabled_member": False,
            "has_pregnant_member": True,
            "has_child_under_5": False,
            "receives_snap": False,
            "receives_medicaid": False,
            "receives_tanf": False,
            "receives_lachip": False,
            "receives_lamoms": False,
            "applicant_age": 27,
            "has_medicare": False,
            "has_other_health_insurance": False,
            "is_louisiana_resident": True,
        },
    },
    {
        "name": "Single adult with low income",
        "features": {
            "household_size": 1,
            "gross_monthly_income": 1200.00,
            "net_monthly_income": 950.00,
            "has_elderly_member": False,
            "has_disabled_member": False,
            "has_pregnant_member": False,
            "has_child_under_5": False,
            "receives_snap": False,
            "receives_medicaid": False,
            "receives_tanf": False,
            "receives_lachip": False,
            "receives_lamoms": False,
            "applicant_age": 25,
            "has_medicare": False,
            "has_other_health_insurance": False,
            "is_louisiana_resident": True,
        },
    },
    {
        "name": "Household with an elderly member",
        "features": {
            "household_size": 2,
            "gross_monthly_income": 2200.00,
            "net_monthly_income": 1400.00,
            "has_elderly_member": True,
            "has_disabled_member": False,
            "has_pregnant_member": False,
            "has_child_under_5": False,
            "receives_snap": False,
            "receives_medicaid": False,
            "receives_tanf": False,
            "receives_lachip": False,
            "receives_lamoms": False,
            "applicant_age": 65,
            "has_medicare": True,
            "has_other_health_insurance": True,
            "is_louisiana_resident": True,
        },
    },
    {
        "name": "Pregnant applicant already receiving Medicaid",
        "features": {
            "household_size": 2,
            "gross_monthly_income": 3000.00,
            "net_monthly_income": 2600.00,
            "has_elderly_member": False,
            "has_disabled_member": False,
            "has_pregnant_member": True,
            "has_child_under_5": False,
            "receives_snap": False,
            "receives_medicaid": True,
            "receives_tanf": False,
            "receives_lachip": False,
            "receives_lamoms": False,
            "applicant_age": 30,
            "has_medicare": False,
            "has_other_health_insurance": False,
            "is_louisiana_resident": True,
        },
    },
    {
        "name": "Infant applying for WIC",
        "features": {
            "household_size": 3,
            "gross_monthly_income": 4000.00,
            "net_monthly_income": 3500.00,
            "has_elderly_member": False,
            "has_disabled_member": False,
            "has_pregnant_member": False,
            "has_child_under_5": True,
            "receives_snap": False,
            "receives_medicaid": False,
            "receives_tanf": False,
            "receives_lachip": True,
            "receives_lamoms": False,
            "applicant_age": 0,
            "has_medicare": False,
            "has_other_health_insurance": False,
            "is_louisiana_resident": True,
        },
    },
    {
        "name": "Child with other health insurance",
        "features": {
            "household_size": 3,
            "gross_monthly_income": 4500.00,
            "net_monthly_income": 3900.00,
            "has_elderly_member": False,
            "has_disabled_member": False,
            "has_pregnant_member": False,
            "has_child_under_5": False,
            "receives_snap": False,
            "receives_medicaid": False,
            "receives_tanf": False,
            "receives_lachip": False,
            "receives_lamoms": False,
            "applicant_age": 8,
            "has_medicare": False,
            "has_other_health_insurance": True,
            "is_louisiana_resident": True,
        },
    },
    {
        "name": "Applicant with a disability",
        "features": {
            "household_size": 2,
            "gross_monthly_income": 1800.00,
            "net_monthly_income": 1500.00,
            "has_elderly_member": False,
            "has_disabled_member": True,
            "has_pregnant_member": False,
            "has_child_under_5": False,
            "receives_snap": False,
            "receives_medicaid": False,
            "receives_tanf": False,
            "receives_lachip": False,
            "receives_lamoms": False,
            "applicant_age": 35,
            "has_medicare": False,
            "has_other_health_insurance": False,
            "is_louisiana_resident": True,
        },
    },
    {
        "name": "Household outside Louisiana",
        "features": {
            "household_size": 3,
            "gross_monthly_income": 2000.00,
            "net_monthly_income": 1700.00,
            "has_elderly_member": False,
            "has_disabled_member": False,
            "has_pregnant_member": False,
            "has_child_under_5": True,
            "receives_snap": False,
            "receives_medicaid": False,
            "receives_tanf": False,
            "receives_lachip": False,
            "receives_lamoms": False,
            "applicant_age": 28,
            "has_medicare": False,
            "has_other_health_insurance": False,
            "is_louisiana_resident": False,
        },
    },
]

for case in test_cases:
    features = case["features"]

    print(f"\n--- {case['name']} ---")
    print("SNAP:", rules.snap_eligibility(features))
    print("WIC:", rules.wic_eligibility(features))
    print("Medicaid:", rules.medicaid_eligibility(features))