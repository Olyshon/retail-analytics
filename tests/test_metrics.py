import pandas as pd
import pytest

from retail_analytics.metrics import SalesMetrics, calculate_metrics


@pytest.fixture
def sales():
    return pd.DataFrame({
        "order_id": ["1001", "1001", "1002"],
        "order_date": ["2026-10-01"] * 3,
        "product_name": ["Кофе", "Чай", "Печенье"],
        "quantity": [2, 1, 3],
        "unit_price": [450, 250, 120],
    })


def test_order_lines_are_not_separate_orders(sales):
    assert calculate_metrics(sales) == SalesMetrics(1510, 2, 755)


def test_empty_data(sales):
    assert calculate_metrics(sales.iloc[:0]) == SalesMetrics(0, 0, 0)


@pytest.mark.parametrize("column,value", [
    ("order_date", "2026-02-30"), ("order_date", "not a date"),
    ("order_date", None), ("order_date", "01/10/2026"),
    ("quantity", "bad"), ("quantity", None), ("quantity", 0),
    ("quantity", -1), ("quantity", float("inf")),
    ("unit_price", "bad"), ("unit_price", None),
    ("unit_price", -1), ("unit_price", float("inf")),
    ("order_id", None), ("order_id", "  "),
])
def test_invalid_values_report_column_and_record(sales, column, value):
    sales[column] = sales[column].astype(object)
    sales.loc[1, column] = value
    with pytest.raises(ValueError, match=column) as error:
        calculate_metrics(sales)
    assert "после заголовка: 2" in str(error.value)


def test_numeric_strings_and_zero_price(sales):
    sales["quantity"] = ["2", "1", "3"]
    sales["unit_price"] = ["0", "250", "120"]
    assert calculate_metrics(sales) == SalesMetrics(610, 2, 305)


def test_input_is_not_modified(sales):
    original = sales.copy(deep=True)
    calculate_metrics(sales)
    pd.testing.assert_frame_equal(sales, original)


def test_missing_column(sales):
    with pytest.raises(ValueError, match="quantity"):
        calculate_metrics(sales.drop(columns="quantity"))


def test_overflow_is_reported(sales):
    sales["quantity"] = 1e308
    with pytest.raises(ValueError, match="слишком велика"):
        calculate_metrics(sales)
