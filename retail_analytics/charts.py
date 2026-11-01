"""Графики из подготовленных таблиц продаж."""

from html import escape
from math import ceil
from textwrap import wrap

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _style_chart(figure: go.Figure) -> go.Figure:
    """Общий светлый стиль; денежные значения и подсказки не меняются."""
    figure.update_layout(
        template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "size": 13, "color": "#202938"},
        colorway=["#2563EB"], margin={"l": 16, "r": 24, "t": 16, "b": 16},
        showlegend=False, hoverlabel={"bgcolor": "white", "font_color": "#202938"},
    )
    figure.update_xaxes(gridcolor="#EEF1F5", zeroline=False, automargin=True)
    figure.update_yaxes(gridcolor="#EEF1F5", zeroline=False, automargin=True)
    return figure


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
    figure.update_traces(line_color="#2563EB", line_width=2.5, marker_size=6)
    figure.update_layout(
        height=280,
        xaxis_type="date", xaxis_tickformat="%d.%m.%Y",
        xaxis_title=None, yaxis_tickformat=",.2f",
    )
    _style_chart(figure)
    # Настройки конкретного графика идут после общего стиля.
    figure.update_layout(margin={"l": 8, "r": 16, "t": 8, "b": 24})
    if not daily.empty:
        first = pd.Timestamp(daily["order_date"].min())
        last = pd.Timestamp(daily["order_date"].max())
        if first == last:
            figure.update_xaxes(
                tickmode="array", tickvals=[first], ticktext=[first.strftime("%d.%m.%Y")],
                range=[first - pd.Timedelta(hours=12), first + pd.Timedelta(hours=12)],
            )
        else:
            figure.update_xaxes(
                tickmode="linear", tick0=first,
                dtick=max(1, ceil((last - first).days / 5)) * 86_400_000,
            )
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
        hovertemplate="Товар: %{y}<br>Выручка: %{customdata[0]}<extra></extra>",
        marker_color="#2563EB",
    )
    # Переносим только подписи: исходные названия и порядок категорий сохраняются.
    lines = [wrap(str(name), width=20) or [""] for name in products["product_name"]]
    labels = ["<br>".join(escape(line) for line in parts) for parts in lines]
    figure.update_layout(
        height=max(200, 90 + sum(max(36, len(parts) * 16 + 18) for parts in lines)),
        bargap=0.35,
        xaxis_tickformat=",.2f",
        yaxis={"type": "category", "categoryorder": "array",
               "categoryarray": products["product_name"].tolist(),
               "autorange": "reversed", "automargin": True},
    )
    _style_chart(figure)
    figure.update_layout(margin={"l": 12, "r": 24, "t": 12, "b": 40})
    figure.update_yaxes(
        title=None, tickmode="array", tickvals=products["product_name"].tolist(),
        ticktext=labels, ticklabelstandoff=12, tickfont_size=12, showgrid=False,
    )
    figure.update_xaxes(title_standoff=16, nticks=5, tickfont_size=12)
    return figure
