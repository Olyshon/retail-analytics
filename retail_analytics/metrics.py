"""Проверка данных и расчёт показателей продаж без зависимости от интерфейса."""

from dataclasses import dataclass
from decimal import Decimal, DecimalException, ROUND_HALF_UP, localcontext
import sys

import pandas as pd


@dataclass(frozen=True)
class SalesMetrics:
    revenue: Decimal
    order_count: int
    average_order_value: Decimal


CENT = Decimal("0.01")
MAX_REVENUE = Decimal(str(sys.float_info.max))


def _decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except DecimalException:
        return Decimal("NaN")


def _sum_money(values) -> Decimal:
    values = list(values)
    with localcontext() as context:
        context.prec = max([28] + [len(value.as_tuple().digits) for value in values]) + len(str(len(values)))
        return sum(values, Decimal("0.00"))


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


def _prepare_sales(data: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Единые проверки и округлённые суммы позиций для обоих расчётов."""
    required = ("order_id", "order_date", "quantity", "unit_price")
    missing = [name for name in required if name not in data.columns]
    if missing:
        raise ValueError("Не хватает обязательных столбцов: " + ", ".join(missing))
    if data.empty:
        return pd.Series(dtype="string"), pd.DataFrame({
            "order_date": pd.Series(dtype="datetime64[ns]"),
            "revenue": pd.Series(dtype=object),
        })

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
        values = data[column].map(_decimal)
        invalid = values.map(lambda value: not value.is_finite())
        if column == "quantity":
            invalid |= values.map(lambda value: value.is_finite() and value <= 0)
            rule = "ожидается положительное конечное число"
        else:
            invalid |= values.map(lambda value: value.is_finite() and value < 0)
            rule = "ожидается неотрицательное конечное число"
        _check_rows(invalid, column, rule)
        numbers[column] = values

    amounts = []
    try:
        for quantity, price in zip(numbers["quantity"], numbers["unit_price"]):
            with localcontext() as context:
                context.prec = max(28, len(quantity.as_tuple().digits) + len(price.as_tuple().digits))
                product = quantity * price
                if product > MAX_REVENUE:
                    raise ValueError("Выручка слишком велика для расчёта. Проверьте quantity и unit_price.")
                context.prec = max(context.prec, product.adjusted() + 3)
                amounts.append(product.quantize(CENT, rounding=ROUND_HALF_UP))
    except DecimalException as error:
        raise ValueError("Выручка слишком велика для расчёта. Проверьте quantity и unit_price.") from error
    if _sum_money(amounts) > MAX_REVENUE:
        raise ValueError("Выручка слишком велика для расчёта. Проверьте quantity и unit_price.")
    return ids, pd.DataFrame({
        "order_date": parsed_dates,
        "revenue": pd.Series(amounts, index=data.index, dtype=object),
    })


def calculate_metrics(data: pd.DataFrame) -> SalesMetrics:
    """Проверить все записи и вернуть показатели; исходные данные не менять."""
    ids, rows = _prepare_sales(data)
    revenue = _sum_money(rows["revenue"])
    order_count = int(ids.nunique())
    with localcontext() as context:
        context.prec = max(28, len(revenue.as_tuple().digits) + len(str(order_count)) + 2)
        average = (revenue / order_count).quantize(CENT, rounding=ROUND_HALF_UP) if order_count else Decimal("0.00")
    return SalesMetrics(revenue, order_count, average)


def daily_revenue(data: pd.DataFrame) -> pd.DataFrame:
    """Выручка по датам продаж, по возрастанию; дни без записей не добавляются."""
    _, rows = _prepare_sales(data)
    if data.empty:
        return pd.DataFrame({
            "order_date": pd.Series(dtype="datetime64[ns]"),
            "revenue": pd.Series(dtype=object),
        })
    return rows.groupby("order_date", as_index=False, sort=True)["revenue"].agg(_sum_money)
