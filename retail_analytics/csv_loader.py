"""Чтение CSV без неявного изменения структуры и значений."""

import csv
from io import StringIO
from typing import BinaryIO

import pandas as pd


def load_sales_csv(source: BinaryIO) -> pd.DataFrame:
    text = source.read().decode("utf-8-sig")
    reader = csv.reader(StringIO(text, newline=""), strict=True)
    try:
        header = next(reader, None)
        if header is None:
            raise pd.errors.EmptyDataError("Пустой CSV")
        if len(header) != len(set(header)):
            raise ValueError("CSV содержит повторяющиеся имена столбцов.")
        records = []
        for number, record in enumerate(reader, start=1):
            if len(record) != len(header):
                raise ValueError(
                    f"Запись {number}: число полей {len(record)} "
                    f"не совпадает с числом заголовков {len(header)}."
                )
            records.append(record)
    except csv.Error as error:
        raise ValueError("Некорректная структура CSV.") from error
    # Все значения остаются текстом: без float и специальных NA-маркеров.
    return pd.DataFrame(records, columns=header, dtype="string")
