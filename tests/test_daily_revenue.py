import pandas as pd
import pytest

from retail_analytics.metrics import calculate_metrics, daily_revenue
from retail_analytics.charts import revenue_chart


@pytest.fixture
def sales():
    return pd.DataFrame({
        "order_id": ["1002", "1001", "1001"],
        "order_date": ["2026-10-03", "2026-10-01", "2026-10-01"],
        "quantity": ["3", "2", "1"],
        "unit_price": ["120", "450", "250"],
    })


def test_daily_totals_sorted_and_match_overall_revenue(sales):
    result = daily_revenue(sales)
    assert result["order_date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-10-01", "2026-10-03",
    ]
    assert result["revenue"].tolist() == [1150, 360]
    assert result["revenue"].sum() == calculate_metrics(sales).revenue


def test_empty_data(sales):
    result = daily_revenue(sales.iloc[:0])
    assert result.empty
    assert result.columns.tolist() == ["order_date", "revenue"]


def test_input_unchanged_with_nondefault_index(sales):
    sales.index = [8, 2, 7]
    original = sales.copy(deep=True)
    assert daily_revenue(sales)["revenue"].tolist() == [1150, 360]
    pd.testing.assert_frame_equal(sales, original)


@pytest.mark.parametrize("column,value", [
    ("order_date", "2026-02-30"), ("quantity", -1), ("unit_price", "bad"),
])
def test_invalid_data_is_rejected(sales, column, value):
    sales[column] = sales[column].astype(object)
    sales.loc[0, column] = value
    with pytest.raises(ValueError, match=column):
        daily_revenue(sales)


def test_single_day_and_zero_revenue_have_visible_marker(sales):
    sales["order_date"] = "2026-10-01"
    sales["unit_price"] = "0"
    result = daily_revenue(sales)
    assert result["revenue"].tolist() == [0]
    chart = revenue_chart(result)
    assert len(chart.data[0].x) == 1
    assert list(chart.data[0].y) == [0]
    assert "markers" in chart.data[0].mode
    assert chart.layout.xaxis.tickmode == "array"
    assert list(chart.layout.xaxis.ticktext) == ["01.10.2026"]
    assert len(chart.layout.xaxis.tickvals) == 1
    assert chart.layout.xaxis.range[0] < result["order_date"].iloc[0] < chart.layout.xaxis.range[1]


def test_multi_day_ticks_never_use_intraday_intervals(sales):
    chart = revenue_chart(daily_revenue(sales))
    assert chart.layout.xaxis.dtick >= 86_400_000
    assert chart.layout.xaxis.tickformat == "%d.%m.%Y"
