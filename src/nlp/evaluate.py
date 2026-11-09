from src.data.schema import FEATURES
from collections import defaultdict, Counter
import json

MONEY_FIELDS = {"gross_monthly_income", "earned_monthly_income", "rent_monthly", "utilities_monthly"}

def load_cases(file_path):
 
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    for case in data:
        for key in case["expected"]:
            if key not in FEATURES:
                raise ValueError(f"{key} not found in FEATURES. Case id = {case['id']}")

    return data

def full_expected(case):
    final_dict = {field_name: case["expected"].get(field_name) for field_name in FEATURES}
    return final_dict

def extract_none(text):
    out_dict = {field_name: None for field_name in FEATURES}
    return out_dict

def values_match(field, expected, actual):
    if expected is None and actual is None:
        return True
    if expected is None or actual is None:
        return False
    if field in MONEY_FIELDS:
        return abs(expected - actual) <= 2
    else:
        return expected == actual

def evaluate(cases, extractor):
    counts = defaultdict(Counter)
    errors = []

    for case in cases:
        exp = full_expected(case)
        got = extractor(case["text"])
        if set(got) != set(FEATURES):
            raise ValueError(f"Case: {case['id']}\nMissing keys: {set(FEATURES) - set(got)}\nExtra keys: {set(got) - set(FEATURES)}\n")
        for field in FEATURES:
            e = exp[field]
            a = got[field]
            if values_match(field, e, a):
                category = "correct"
            elif e is None:
                category = "invented"                
            elif a is None:
                category = "missed"
            else:
                category = "wrong"
            counts[field][category] += 1
            if category != "correct":
                errors.append((case["id"], field, category, e, a))

    return counts, errors

def print_report(counts, errors, cases):
    n_cases = len(cases)
    labeled_total = sum(v is not None for case in cases for v in full_expected(case).values())
    col_names = ["Feature", "Correct", "Invented", "Missed", "Wrong", "Accuracy"]
    header_row = f"| {col_names[0]:<28} | {col_names[1]:>8} | {col_names[2]:>8} | {col_names[3]:>8} | {col_names[4]:>8} | {col_names[5]:>8} |"
    total = Counter()


    print("-" * len(header_row))
    print(header_row)
    print("-" * len(header_row))

    for field in FEATURES:
        c = counts[field]
        total.update(c)
        acc = c["correct"] / n_cases
        print(f"| {field:<28} | {c['correct']:>8} | {c['invented']:>8} | {c['missed']:>8} | {c['wrong']:>8} | {acc:>8.1%} |")

    overall_accuracy = total["correct"] / (n_cases * len(FEATURES))
    labeled_value_accuracy = (labeled_total - total["missed"] - total["wrong"]) / labeled_total
    print("-" * len(header_row))
    print(f"Overall accuracy: {overall_accuracy:.1%} ({total['correct']} / {n_cases * len(FEATURES)})")
    print(f"Labeled-value accuracy: {labeled_value_accuracy:.1%} ({labeled_total - total['missed'] - total['wrong']} / {labeled_total})")
    print("\nErrors:\n")

    for e in errors[:20]:
        print(f"{e}")
    print(f"Showing {min(20, len(errors))} of {len(errors)} errors.")

if __name__ == "__main__":
    cases = load_cases("tests/data/extraction_cases.json")
    print(len(cases))
    #print(full_expected(cases[20]))
    # print(values_match("rent_monthly", 950, 951))
    # print(values_match("rent_monthly", 950, 960))
    # print(values_match("receives_snap", True, None))
    # print(values_match("household_size", None, None))
    counts, errors = evaluate(cases, extract_none)
    # print(counts["household_size"])
    # print(f"Length of errors: {len(errors)}")
    print_report(counts, errors, cases)