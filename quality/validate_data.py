
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CHUNK_SIZE = 100_000


def load_ids(filename, column):
    """Load a reference key column as strings."""
    df = pd.read_csv(
        RAW / filename,
        usecols=[column],
        dtype={column: "string"}
    )
    return set(df[column].dropna())


def check_foreign_key(filename, column, valid_ids):
    """Count foreign-key values that have no matching parent."""
    invalid = 0
    missing = 0
    total = 0

    for chunk in pd.read_csv(
        RAW / filename,
        usecols=[column],
        dtype={column: "string"},
        chunksize=CHUNK_SIZE
    ):
        total += len(chunk)
        missing += int(chunk[column].isna().sum())
        invalid += int(
            (~chunk[column].isin(valid_ids)
             & chunk[column].notna()).sum()
        )

    print(
        f"{filename}.{column}: "
        f"rows={total:,}, missing={missing:,}, "
        f"invalid references={invalid:,}"
    )

    return missing == 0 and invalid == 0


def check_nonnegative(filename, column):
    """Check whether a numeric column contains negative values."""
    invalid = 0
    missing = 0

    for chunk in pd.read_csv(
        RAW / filename,
        usecols=[column],
        chunksize=CHUNK_SIZE
    ):
        values = pd.to_numeric(chunk[column], errors="coerce")
        missing += int(values.isna().sum())
        invalid += int((values < 0).sum())

    print(
        f"{filename}.{column}: "
        f"missing/unparseable={missing:,}, negative={invalid:,}"
    )

    return missing == 0 and invalid == 0


def main():
    print("FOODFLOW DATA VALIDATION")
    print("=" * 60)

    # Reference IDs used to validate relationships
    user_ids = load_ids("users.csv", "user_id")
    restaurant_ids = load_ids(
        "restaurants.csv", "restaurant_id"
    )
    menu_ids = load_ids("menu.csv", "menu_id")
    order_ids = load_ids("orders.csv", "order_id")

    results = {}

    # Foreign-key checks
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

    # Numeric value checks
    results["menu.price"] = check_nonnegative(
        "menu.csv", "price"
    )
    results["orders.total_amount"] = check_nonnegative(
        "orders.csv", "total_amount"
    )
    results["order_items.price"] = check_nonnegative(
        "order_items.csv", "price"
    )

    # Quantity must be strictly positive
    quantity_invalid = 0
    quantity_missing = 0

    for chunk in pd.read_csv(
        RAW / "order_items.csv",
        usecols=["quantity"],
        chunksize=CHUNK_SIZE
    ):
        quantity = pd.to_numeric(
            chunk["quantity"], errors="coerce"
        )
        quantity_missing += int(quantity.isna().sum())
        quantity_invalid += int((quantity <= 0).sum())

    results["order_items.quantity"] = (
        quantity_missing == 0 and quantity_invalid == 0
    )

    print(
        "\norder_items.quantity: "
        f"missing/unparseable={quantity_missing:,}, "
        f"zero-or-negative={quantity_invalid:,}"
    )

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")

    for name, passed in results.items():
        print(f"{'PASS' if passed else 'FAIL'} - {name}")

    failed = [name for name, passed in results.items() if not passed]

    print(f"\nPassed: {len(results) - len(failed)}/{len(results)}")

    if failed:
        print("Investigate the failed checks before loading the data.")
    else:
        print("All implemented checks passed.")


if __name__ == "__main__":
    main()
