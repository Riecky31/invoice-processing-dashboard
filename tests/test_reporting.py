import os

import pandas as pd

os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///:memory:",
)

from app.services.reporting import (  # noqa: E402
    get_business_unit_summary,
    get_staff_summary,
)
from app.services.reporting.metrics import (  # noqa: E402
    calculate_tat_metrics,
)


def test_reporting_package_exports_staff_and_business_summaries():
    df = pd.DataFrame(
        {
            "user_id": ["alice", "bob", None],
            "business_unit": ["Finance", "Finance", "HR"],
            "invoice_number": ["A1", "B1", "C1"],
            "invoice_amount": [100, 200, 50],
            "vendor_name": ["Vendor A", "Vendor B", "Vendor A"],
        }
    )

    staff = get_staff_summary(df)
    business_units = get_business_unit_summary(df)

    assert set(staff["user_id"]) == {
        "alice",
        "bob",
        "Unknown",
    }
    assert business_units.loc[
        business_units["business_unit"] == "Finance",
        "invoices",
    ].item() == 2


def test_tat_metrics_include_dashboard_keys_and_sla_percentage():
    metrics = calculate_tat_metrics(
        pd.DataFrame(
            {
                "tat_minutes": [
                    60,
                    24 * 60,
                    25 * 60,
                    None,
                    -1,
                ]
            }
        )
    )

    assert metrics["tat_count"] == 3
    assert metrics["sla_percentage"] == 66.67
    assert metrics["minimum_tat_hours"] == 1.0
    assert metrics["maximum_tat_hours"] == 25.0


def test_tat_metrics_include_dashboard_keys_without_tat_data():
    metrics = calculate_tat_metrics(
        pd.DataFrame({"tat_minutes": [None]})
    )

    assert metrics["sla_percentage"] is None
    assert metrics["minimum_tat_hours"] is None
    assert metrics["maximum_tat_hours"] is None
