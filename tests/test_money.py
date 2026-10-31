from decimal import Decimal

import pandas as pd
import pytest

from retail_analytics.metrics import calculate_metrics, daily_revenue
from retail_analytics.charts import revenue_chart


@pytest.mark.parametrize("quantities,prices,dates,expected", [
    (["2", "0.5", "2"], ["70.05", "35.45", "6.80"],
     ["2026-10-01"] * 3, [Decimal("171.43")]),
    (["1", "1", "1"], ["0.005", "0.005", "0.004"],
     ["2026-10-02", "2026-10-01", "2026-10-01"],
     [Decimal("0.01"), Decimal("0.01")]),
])
def test_line_rounding_and_exact_daily_total(quantities, prices, dates, expected):
    data = pd.DataFrame({"order_id": ["001"] * 3, "order_date": dates,
                         "quantity": quantities, "unit_price": prices})
    metrics = calculate_metrics(data)
    daily = daily_revenue(data)
    assert isinstance(metrics.revenue, Decimal)
    assert daily["revenue"].tolist() == expected
    assert metrics.revenue == sum(expected) == sum(daily["revenue"])
    assert metrics.average_order_value == metrics.revenue
    assert f'{metrics.revenue:.2f}' == f'{sum(daily["revenue"]):.2f}'
    chart = revenue_chart(daily)
    assert [f"{value:.2f}" for value in chart.data[0].y] == [f"{value:.2f}" for value in expected]
    assert [row[0] for row in chart.data[0].customdata] == [f"{value:,.2f}" for value in expected]
    chart.to_json()  # Проверяем также сериализацию Decimal для Streamlit.
