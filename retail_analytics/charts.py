"""Графики из подготовленных таблиц продаж."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def revenue_chart(daily: pd.DataFrame) -> go.Figure:
    """Линия с маркерами: видна в том числе единственная дата продаж."""
    figure = px.line(
        daily.assign(revenue_label=daily["revenue"].map(lambda value: f"{value:,.2f}")),
        x="order_date",
        y="revenue",
        markers=True,
        custom_data=["revenue_label"],
        labels={"order_date": "Дата", "revenue": "Выручка"},
    )
    figure.update_traces(hovertemplate="Дата: %{x|%Y-%m-%d}<br>Выручка: %{customdata[0]}<extra></extra>")
    figure.update_layout(xaxis_type="date", yaxis_tickformat=",.2f")
    return figure


def top_products_chart(products: pd.DataFrame) -> go.Figure:
    """Горизонтальные столбцы; первый товар рейтинга отображается сверху."""
    figure = px.bar(
        products.assign(revenue_label=products["revenue"].map(lambda value: f"{value:,.2f}")),
        x="revenue",
        y="product_name",
        orientation="h",
        custom_data=["revenue_label"],
        labels={"product_name": "Товар", "revenue": "Выручка"},
    )
    figure.update_traces(
        hovertemplate="Товар: %{y}<br>Выручка: %{customdata[0]}<extra></extra>"
    )
    figure.update_layout(
        height=max(350, 45 * len(products) + 120),
        xaxis_tickformat=",.2f",
        yaxis={"type": "category", "categoryorder": "array",
               "categoryarray": products["product_name"].tolist(),
               "autorange": "reversed", "automargin": True},
    )
    return figure
