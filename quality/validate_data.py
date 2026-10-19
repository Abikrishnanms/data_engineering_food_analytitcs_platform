
import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "data" / "processed"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 100_000

# Allowed values should be confirmed against the actual dataset.
ALLOWED_STATUSES = {"Delivered", "Cancelled"}
ALLOWED_PAYMENT_METHODS = {
    "UPI",
    "Credit Card",
    "Debit Card",
    "Cash on Delivery",
    "Wallet",
}


def load_ids(filename, column):
    df = pd.read_csv(
        RAW / filename,
        usecols=[column],
        dtype={column: "string"},
    )
    return set(df[column].dropna())


def check_foreign_key(filename, column, valid_ids):
    invalid = 0
    missing = 0
    total = 0

    for chunk in pd.read_csv(
        RAW / filename,
        usecols=[column],
        dtype={column: "string"},
        chunksize=CHUNK_SIZE,
    ):
        total += len(chunk)
        missing += int(chunk[column].isna().sum())
        invalid += int(
            (~chunk[column].isin(valid_ids) & chunk[column].notna()).sum()
        )

    print(
        f"{filename}.{column}: rows={total:,}, "
        f"missing={missing:,}, invalid references={invalid:,}"
    )
    return missing == 0 and invalid == 0


def check_nonnegative(filename, column):
    invalid = 0
    missing = 0

    for chunk in pd.read_csv(
        RAW / filename,
        usecols=[column],
        chunksize=CHUNK_SIZE,
    ):
        values = pd.to_numeric(chunk[column], errors="coerce")
        missing += int(values.isna().sum())
        invalid += int((values < 0).sum())

    print(
        f"{filename}.{column}: "
        f"missing/unparseable={missing:,}, negative={invalid:,}"
    )
    return missing == 0 and invalid == 0


def check_positive_quantity():
    invalid = 0
    missing = 0

    for chunk in pd.read_csv(
        RAW / "order_items.csv",
        usecols=["quantity"],
        chunksize=CHUNK_SIZE,
    ):
        quantity = pd.to_numeric(chunk["quantity"], errors="coerce")
        missing += int(quantity.isna().sum())
        invalid += int((quantity <= 0).sum())

    print(
        f"order_items.quantity: "
        f"missing/unparseable={missing:,}, zero-or-negative={invalid:,}"
    )
    return missing == 0 and invalid == 0


def check_datetime_column(filename, column, date_format):
    invalid = 0
    missing = 0
    total = 0

    for chunk in pd.read_csv(
        RAW / filename,
        usecols=[column],
        dtype={column: "string"},
        chunksize=CHUNK_SIZE,
    ):
        values = chunk[column].str.strip()
        missing += int(values.isna().sum() + values.eq("").sum())
        parsed = pd.to_datetime(values, format=date_format, errors="coerce")
        invalid += int((parsed.isna() & values.notna() & values.ne("")).sum())
        total += len(chunk)

    print(
        f"{filename}.{column}: rows={total:,}, "
        f"missing/blank={missing:,}, invalid format/value={invalid:,}"
    )
    return missing == 0 and invalid == 0


def check_numeric_range(filename, column, minimum, maximum):
    invalid = 0
    missing = 0
    total = 0

    for chunk in pd.read_csv(
        RAW / filename,
        usecols=[column],
        chunksize=CHUNK_SIZE,
    ):
        values = pd.to_numeric(chunk[column], errors="coerce")
        missing += int(values.isna().sum())
        invalid += int(((values < minimum) | (values > maximum)).sum())
        total += len(chunk)

    print(
        f"{filename}.{column}: rows={total:,}, "
        f"missing/unparseable={missing:,}, "
        f"outside [{minimum}, {maximum}]={invalid:,}"
    )
    return missing == 0 and invalid == 0


def check_binary_flag(filename, column):
    invalid = 0
    missing = 0
    total = 0

    for chunk in pd.read_csv(
        RAW / filename,
        usecols=[column],
        chunksize=CHUNK_SIZE,
    ):
        values = pd.to_numeric(chunk[column], errors="coerce")
        missing += int(values.isna().sum())
        invalid += int((~values.isin([0, 1]) & values.notna()).sum())
        total += len(chunk)

    print(
        f"{filename}.{column}: rows={total:,}, "
        f"missing/unparseable={missing:,}, non-binary={invalid:,}"
    )
    return missing == 0 and invalid == 0


def check_allowed_values(filename, column, allowed_values):
    invalid_count = 0
    missing = 0
    unexpected_values = set()
    total = 0

    for chunk in pd.read_csv(
        RAW / filename,
        usecols=[column],
        dtype={column: "string"},
        chunksize=CHUNK_SIZE,
    ):
        values = chunk[column].str.strip()
        missing += int(values.isna().sum() + values.eq("").sum())
        total += len(chunk)

        unexpected = values[
            values.notna()
            & values.ne("")
            & ~values.isin(allowed_values)
        ]
        invalid_count += len(unexpected)
        unexpected_values.update(unexpected.unique().tolist())

    print(
        f"{filename}.{column}: rows={total:,}, "
        f"missing/blank={missing:,}, invalid values={invalid_count:,}"
    )

    if unexpected_values:
        print(f"  Unexpected values: {sorted(unexpected_values)}")

    return missing == 0 and invalid_count == 0


def main():
    print("FOODFLOW DATA VALIDATION")
    print("=" * 65)

    user_ids = load_ids("users.csv", "user_id")
    restaurant_ids = load_ids("restaurants.csv", "restaurant_id")
    menu_ids = load_ids("menu.csv", "menu_id")
    order_ids = load_ids("orders.csv", "order_id")

    results = {}

    # Existing foreign-key checks
    results["orders.user_id"] = check_foreign_key(
        "orders.csv", "user_id", user_ids
    )
    results["orders.restaurant_id"] = check_foreign_key(
        "orders.csv", "restaurant_id", restaurant_ids
    )
    results["menu.restaurant_id"] = check_foreign_key(
        "menu.csv", "restaurant_id", restaurant_ids
    )
    results["order_items.order_id"] = check_foreign_key(
        "order_items.csv", "order_id", order_ids
    )
    results["order_items.menu_id"] = check_foreign_key(
        "order_items.csv", "menu_id", menu_ids
    )

    # Existing numeric checks
    results["menu.price"] = check_nonnegative("menu.csv", "price")
    results["orders.total_amount"] = check_nonnegative(
        "orders.csv", "total_amount"
    )
    results["order_items.price"] = check_nonnegative(
        "order_items.csv", "price"
    )
    results["order_items.quantity"] = check_positive_quantity()

    # New date and time checks
    results["orders.order_date"] = check_datetime_column(
        "orders.csv", "order_date", "%Y-%m-%d"
    )
    results["orders.delivery_time"] = check_datetime_column(
        "orders.csv", "delivery_time", "%H:%M:%S"
    )

    # New range and flag checks
    results["restaurants.rating"] = check_numeric_range(
        "restaurants.csv", "rating", 0, 5
    )
    results["menu.is_veg"] = check_binary_flag("menu.csv", "is_veg")
    results["restaurants.is_cloud_kitchen"] = check_binary_flag(
        "restaurants.csv", "is_cloud_kitchen"
    )

    # New allowed-value checks
    results["orders.order_status"] = check_allowed_values(
        "orders.csv", "order_status", ALLOWED_STATUSES
    )
    results["orders.payment_method"] = check_allowed_values(
        "orders.csv", "payment_method", ALLOWED_PAYMENT_METHODS
    )

    print("\n" + "=" * 65)
    print("VALIDATION SUMMARY")

    for name, passed in results.items():
        print(f"{'PASS' if passed else 'FAIL'} - {name}")

    failed = [name for name, passed in results.items() if not passed]
    passed_count = len(results) - len(failed)

    print(f"\nPassed: {passed_count}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")

    # Save the results for documentation and later pipeline use.
    report = {
        "total_checks": len(results),
        "passed": passed_count,
        "failed": len(failed),
        "all_passed": len(failed) == 0,
        "checks": {
            name: "PASS" if passed else "FAIL"
            for name, passed in results.items()
        },
    }

    report_path = REPORT_DIR / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nValidation report saved to: {report_path}")

    if failed:
        print("\nInvestigate failed checks before loading data.")
    else:
        print("\nAll implemented checks passed.")


if __name__ == "__main__":
    main()
