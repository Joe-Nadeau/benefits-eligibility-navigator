# Data contract

## Household input fields

The field list lives in [`src/data/schema.py`](../src/data/schema.py).
Per-program feature subsets are in [`src/data/features.py`](../src/data/features.py).

## Extraction and labeling rules

1. Money is monthly. Convert yearly amounts to monthly by dividing by 12. Round approximate amounts ("about 2 grand") to their stated value.

2. Gross income is filled only if every income source has an amount; otherwise null.

3. Household size: count when the sentence presents the whole household. An unborn child is not counted.

4. false only for an explicit negative ("no one is disabled"). Something that simply isn’t mentioned stays null. The same applies to 0 for money: only when stated ("not working", "no mortgage").

5. Rent that includes utilities: `utilities_monthly` stays null.

6. Age-based fields (`has_elderly_member`, `has_child_under_5`) are true if any household member's stated age qualifies (60+, or under 5). They are false only if the whole household is listed with ages and no one qualifies. Otherwise they stay null.

7. `applicant_age` is the speaker’s age.

8. A Louisiana city or parish counts as residency. A city that only might be in Louisiana doesn’t.

9. Benefits: `receives_*` is true only for current receipt ("we get SNAP"), not for "applied" or "used to get."

10. Wage income goes in earned income. VA benefits, unemployment, child support, Social Security and SSI are unearned: they count toward gross, never toward earned.

11. A mortgage is recorded in `rent_monthly`.

12. Disability: true if the person is called disabled, receives disability benefits, can’t work because of a condition, or is legally blind.

13. Weekly, biweekly and hourly pay is converted using 4.33 weeks/month. Hourly pay requires stated hours ("full time" alone → null). Round money to the nearest dollar.

14. Current receipt of WIC, Social Security or SSI isn’t recorded: there’s no input field for it.

## Program list

## Prediction output (program -> probability)

## Missing/noisy fields
