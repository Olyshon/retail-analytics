from decimal import Decimal
from io import BytesIO
from pathlib import Path
import runpy
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from retail_analytics.metrics import calculate_metrics


HEADER = "order_id,order_date,product_name,quantity,unit_price\n"


def run_upload(csv):
    streamlit = MagicMock()
    streamlit.file_uploader.return_value = BytesIO(csv.encode("utf-8-sig"))
    def columns(count):
        result = [MagicMock() for _ in range(count)]
        for column in result:
            column.date_input.side_effect = lambda *args, **kwargs: kwargs["value"]
        return result

    streamlit.columns.side_effect = columns
    methods = ("set_page_config", "title", "write", "caption", "file_uploader",
               "error", "warning", "columns", "subheader", "plotly_chart", "dataframe")
    with patch.multiple(st, **{name: getattr(streamlit, name) for name in methods}):
        namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "app.py"))
    return streamlit, namespace


@pytest.mark.parametrize("csv", [
    HEADER + "1001,1002,2026-10-01,123,2,100\n",
    HEADER + "1001,2026-10-01,Coffee,1\n",
    HEADER + "1001,2026-10-01,Coffee,1,10\n1002,2026-10-02,Tea,2,20,extra\n",
    "order_id,order_date,product_name,quantity,quantity,unit_price\n"
    "1001,2026-10-01,Coffee,1,100,10\n",
    HEADER.rstrip("\n") + ",note,note\n1001,2026-10-01,Coffee,1,10,a,b\n",
], ids=["extra-field", "missing-field", "unequal-records", "duplicate-quantity", "duplicate-extra-header"])
def test_malformed_csv_is_rejected_before_calculation(csv):
    ui, _ = run_upload(csv)
    ui.error.assert_called_once()
    ui.columns.assert_not_called()
    ui.plotly_chart.assert_not_called()


@pytest.mark.parametrize("identifier", ["NA", "NULL", "N/A", "00123"])
def test_text_order_ids_survive_csv_loading(identifier):
    ui, namespace = run_upload(HEADER + f"{identifier},2026-10-01,Coffee,1,10\n")
    ui.error.assert_not_called()
    assert namespace["data"]["order_id"].tolist() == [identifier]
    assert calculate_metrics(namespace["data"]).order_count == 1


@pytest.mark.parametrize("identifier", ["", "   "])
def test_empty_order_id_is_still_rejected(identifier):
    ui, _ = run_upload(HEADER + f"{identifier},2026-10-01,Coffee,1,10\n")
    ui.error.assert_called_once()
    ui.columns.assert_not_called()


def test_quoted_commas_quotes_and_multiline_fields_are_valid():
    ui, namespace = run_upload(HEADER + '001,2026-10-01,"Coffee, ""special""\nlarge",1,10\n')
    ui.error.assert_not_called()
    assert namespace["data"]["product_name"].tolist() == ['Coffee, "special"\nlarge']


def test_decimal_precision_survives_csv_loading():
    ui, namespace = run_upload(HEADER + "001,2026-10-01,Coffee,1,1.00499999999999999999999999999\n")
    ui.error.assert_not_called()
    assert calculate_metrics(namespace["data"]).revenue == Decimal("1.00")
