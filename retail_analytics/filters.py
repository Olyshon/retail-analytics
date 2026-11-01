"""Фильтрация проверенных продаж без изменения исходной таблицы."""

from datetime import date

import pandas as pd


def filter_by_date(data: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    """Вернуть записи периода, включая обе границы; даты CSV — YYYY-MM-DD."""
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if pd.isna(start) or pd.isna(end):
        raise ValueError("Выберите начальную и конечную дату.")
    if start > end:
        raise ValueError("Начальная дата не должна быть позже конечной.")
    dates = pd.to_datetime(data["order_date"], format="%Y-%m-%d", errors="raise")
    return data.loc[dates.between(start, end, inclusive="both")].copy()
