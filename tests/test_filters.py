from datetime import date

import pandas as pd
import pytest

from retail_analytics.filters import filter_by_date
from retail_analytics.metrics import calculate_metrics, daily_revenue


@pytest.fixture
def sales():
    return pd.DataFrame({
        "order_id": ["1", "2", "2", "3"],
        "order_date": ["2026-10-01", "2026-10-03", "2026-10-03", "2026-10-05"],
        "quantity": ["1", "2", "1", "3"],
        "unit_price": ["10.005", "20", "5", "10"],
    }, index=[8, 4, 2, 9])


def test_both_boundaries_included(sales):
    result = filter_by_date(sales, date(2026, 10, 1), date(2026, 10, 3))
    assert result.index.tolist() == [8, 4, 2]


def test_same_day_keeps_all_repeated_dates(sales):
    result = filter_by_date(sales, date(2026, 10, 3), date(2026, 10, 3))
    assert result.index.tolist() == [4, 2]
    metrics = calculate_metrics(result)
    assert metrics.revenue == 45
    assert metrics.order_count == 1
    assert metrics.average_order_value == 45
    assert daily_revenue(result)["revenue"].tolist() == [45]


def test_full_range_preserves_data_and_money(sales):
    result = filter_by_date(sales, date(2026, 10, 1), date(2026, 10, 5))
    pd.testing.assert_frame_equal(result, sales)
    assert calculate_metrics(result) == calculate_metrics(sales)


def test_empty_period_returns_zero_metrics(sales):
    result = filter_by_date(sales, date(2026, 10, 2), date(2026, 10, 2))
    assert result.empty
    assert result.columns.tolist() == sales.columns.tolist()
    metrics = calculate_metrics(result)
    assert metrics.revenue == metrics.order_count == metrics.average_order_value == 0
    assert daily_revenue(result).empty


def test_empty_source(sales):
    assert filter_by_date(sales.iloc[:0], date(2026, 10, 1), date(2026, 10, 5)).empty


def test_reversed_range(sales):
    with pytest.raises(ValueError, match="Начальная дата"):
        filter_by_date(sales, date(2026, 10, 5), date(2026, 10, 1))


def test_input_is_not_modified(sales):
    original = sales.copy(deep=True)
    result = filter_by_date(sales, date(2026, 10, 3), date(2026, 10, 3))
    result.loc[4, "unit_price"] = "999"
    pd.testing.assert_frame_equal(sales, original)
