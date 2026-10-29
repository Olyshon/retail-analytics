"""Проверка данных и расчёт показателей продаж без зависимости от интерфейса."""

from dataclasses import dataclass
import math

import pandas as pd


@dataclass(frozen=True)
class SalesMetrics:
    revenue: float
    order_count: int
    average_order_value: float


def _check_rows(invalid: pd.Series, column: str, rule: str) -> None:
    if invalid.any():
        positions = [str(i + 1) for i, bad in enumerate(invalid) if bad]
        rows = ", ".join(positions[:10])
        if len(positions) > 10:
            rows += ", …"
        raise ValueError(
            f"Некорректные значения в {column}: {rule}. "
            f"Номера записей после заголовка: {rows}."
        )


def calculate_metrics(data: pd.DataFrame) -> SalesMetrics:
    """Проверить все записи и вернуть показатели; исходные данные не менять."""
    required = ("order_id", "order_date", "quantity", "unit_price")
    missing = [name for name in required if name not in data.columns]
    if missing:
        raise ValueError("Не хватает обязательных столбцов: " + ", ".join(missing))
    if data.empty:
        return SalesMetrics(0.0, 0, 0.0)

    ids = data["order_id"].astype("string").str.strip()
    _check_rows(ids.isna() | ids.eq(""), "order_id", "идентификатор не должен быть пустым")

    dates = data["order_date"].astype("string")
    parsed_dates = pd.to_datetime(dates, format="%Y-%m-%d", errors="coerce")
    _check_rows(
        ~dates.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False) | parsed_dates.isna(),
        "order_date", "ожидается существующая дата в формате YYYY-MM-DD",
    )

    numbers = {}
    for column in ("quantity", "unit_price"):
        values = pd.to_numeric(data[column], errors="coerce").astype(float)
        invalid = ~values.map(math.isfinite)
        if column == "quantity":
            invalid |= values.le(0)
            rule = "ожидается положительное конечное число"
        else:
            invalid |= values.lt(0)
            rule = "ожидается неотрицательное конечное число"
        _check_rows(invalid, column, rule)
        numbers[column] = values

    revenue = float((numbers["quantity"] * numbers["unit_price"]).sum())
    if not math.isfinite(revenue):
        raise ValueError("Выручка слишком велика для расчёта. Проверьте quantity и unit_price.")
    order_count = int(ids.nunique())
    return SalesMetrics(revenue, order_count, revenue / order_count if order_count else 0.0)
