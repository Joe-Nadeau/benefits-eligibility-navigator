from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.rules.snap_eligibility import snap_eligibility

app = FastAPI(title="SNAP Income Screening Demo")
Money = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


class Household(BaseModel):
    household_size: int = Field(ge=1)
    gross_monthly_income: Money
    earned_monthly_income: Money
    rent_monthly: Money
    has_elderly_member: bool
    has_disabled_member: bool


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).resolve().parents[2] / "frontend" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/estimate/snap")
def estimate(household: Household):
    if household.earned_monthly_income > household.gross_monthly_income:
        raise HTTPException(422, "Income from work must be at most total household income.")

    # USDA FY 2027 standard deduction and excess shelter cap.
    standard = {4: 229, 5: 268, 6: 308}.get(min(household.household_size, 6), 217)
    adjusted = max(Decimal(0), household.gross_monthly_income
                   - household.earned_monthly_income * Decimal("0.20") - standard)
    shelter = max(Decimal(0), household.rent_monthly - adjusted / 2)
    if not (household.has_elderly_member or household.has_disabled_member):
        shelter = min(shelter, Decimal(769))

    net = max(Decimal(0), adjusted - shelter).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    features = household.model_dump()
    features["net_monthly_income"] = net
    result = snap_eligibility(features)
    return {
        "passes_income_screen": result["eligible"],
        "reason": result["reason"],
        "net_monthly_income": str(net),
    }
