from decimal import Decimal

import pandas as pd

from retail_analytics.metrics import top_products, calculate_metrics
from retail_analytics.charts import top_products_chart


def sales(names, prices):
    return pd.DataFrame({
        "order_id": [str(i) for i in range(len(names))],
        "order_date": ["2026-10-01"] * len(names),
        "product_name": names,
        "quantity": ["1"] * len(names),
        "unit_price": prices,
    })


def test_repeated_products_sum_all_rows_without_changing_source():
    data = sales(["Кофе", "Чай", "Кофе"], ["450", "250", "900"])
    data.index = [8, 2, 5]
    original = data.copy(deep=True)
    result = top_products(data)
    assert result["product_name"].tolist() == ["Кофе", "Чай"]
    assert result["revenue"].tolist() == [Decimal("1350.00"), Decimal("250.00")]
    assert sum(result["revenue"]) == calculate_metrics(data).revenue
    pd.testing.assert_frame_equal(data, original)


def test_equal_revenue_sorted_by_name():
    result = top_products(sales(["Чай", "Кофе", "Печенье"], ["10", "10", "10"]))
    assert result["product_name"].tolist() == ["Кофе", "Печенье", "Чай"]


def test_top_ten_limit_and_tie_at_boundary():
    names = [f"Товар {i:02}" for i in reversed(range(12))]
    result = top_products(sales(names, ["10"] * 12))
    assert len(result) == 10
    assert result["product_name"].tolist() == sorted(names)[:10]


def test_revenue_sorted_descending_before_limiting():
    result = top_products(sales([str(i) for i in range(12)], [str(i) for i in range(12)]))
    assert result["revenue"].tolist() == [Decimal(i) for i in reversed(range(2, 12))]


def test_fractional_money_uses_per_line_half_up_and_exact_decimal():
    data = sales(["A", "A", "B", "C"], ["0.005", "0.005", "0.014", "1.00499999999999999999999999999"])
    data["quantity"] = ["1", "1", "1", "1"]
    result = top_products(data)
    assert result["product_name"].tolist() == ["C", "A", "B"]
    assert result["revenue"].tolist() == [Decimal("1.00"), Decimal("0.02"), Decimal("0.01")]
    assert all(isinstance(value, Decimal) for value in result["revenue"])


def test_fractional_quantity():
    data = sales(["A", "A"], ["0.10", "0.10"])
    data["quantity"] = ["1.25", "1.25"]
    assert top_products(data)["revenue"].tolist() == [Decimal("0.26")]


def test_empty_selection():
    result = top_products(sales([], []))
    assert result.empty
    assert result.columns.tolist() == ["product_name", "revenue"]


def test_horizontal_chart_preserves_order_and_exact_hover_amounts():
    result = top_products(sales(["Кофе", "Чай"], ["1.005", "2"]))
    chart = top_products_chart(result)
    assert chart.data[0].orientation == "h"
    assert list(chart.data[0].y) == ["Чай", "Кофе"]
    assert chart.layout.yaxis.autorange == "reversed"
    assert chart.data[0].customdata.tolist() == [["2.00"], ["1.01"]]


def test_long_labels_are_wrapped_without_losing_names():
    name = "Очень длинное название товара с подробным описанием и характеристиками"
    chart = top_products_chart(top_products(sales([name], ["1.005"])))
    assert list(chart.data[0].y) == [name]
    assert chart.layout.yaxis.ticktext[0].replace("<br>", " ") == name
    assert chart.layout.yaxis.automargin
    assert chart.data[0].customdata.tolist() == [["1.01"]]


def test_small_ranking_is_more_compact_than_ten_products():
    small = top_products_chart(top_products(sales(["A", "B", "C"], ["1"] * 3)))
    large = top_products_chart(top_products(sales([str(i) for i in range(10)], ["1"] * 10)))
    assert small.layout.height < large.layout.height
