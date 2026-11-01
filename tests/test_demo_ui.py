from datetime import date
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from retail_analytics.csv_loader import load_sales_csv
from retail_analytics.metrics import calculate_metrics


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SAMPLE = ROOT / "data" / "sample_sales.csv"
USER_CSV = (
    b"order_id,order_date,product_name,quantity,unit_price\n"
    b"001,2026-11-01,Test,2,15.005\n"
)


def run(app, upload=None):
    with patch("streamlit.file_uploader", return_value=BytesIO(upload) if upload is not None else None) as uploader:
        app.run(timeout=30)
        if app.button_group[0].value == "Мой CSV":
            uploader.assert_called_once()
        else:
            uploader.assert_not_called()
    assert not app.exception
    return app


def test_default_demo_uses_repository_data_and_download(monkeypatch, tmp_path):
    # Cloud-compatible path: the process need not start in the project directory.
    monkeypatch.chdir(tmp_path)
    with patch("streamlit.download_button", return_value=False) as download:
        app = run(AppTest.from_file(APP))
    assert app.button_group[0].value == "Демо-данные"
    assert not app.get("file_uploader")
    assert not app.button
    expected = calculate_metrics(load_sales_csv(BytesIO(SAMPLE.read_bytes())))
    assert [m.value for m in app.metric] == [
        f"{expected.revenue:,.2f}", str(expected.order_count), f"{expected.average_order_value:,.2f}",
    ]
    assert len(app.get("plotly_chart")) == 2
    assert len(app.date_input) == 2
    assert len(app.dataframe[0].value) == 10
    assert any("Синтетические продажи" in item.value for item in app.caption)
    assert not any("Обязательные столбцы" in item.value for item in app.caption)
    assert download.call_args.kwargs["data"] == SAMPLE.read_bytes()
    assert download.call_args.kwargs["file_name"] == "sample_sales.csv"
    app.date_input[1].set_value(date(2026, 10, 1))
    run(app)
    assert app.metric[0].value == "1,150.00"


def test_switch_between_uploaded_file_and_demo():
    app = run(AppTest.from_file(APP), USER_CSV)
    assert app.button_group[0].value == "Демо-данные"
    assert not app.get("file_uploader")
    app.button_group[0].set_value("Мой CSV")
    run(app, USER_CSV)
    assert app.metric[0].value == "30.01"
    assert not app.get("download_button")
    assert any("Обязательные столбцы" in item.value for item in app.caption)
    app.button_group[0].set_value("Демо-данные")
    run(app, USER_CSV)
    assert app.button_group[0].value == "Демо-данные"
    assert app.date_input[0].value == date(2026, 10, 1)
    assert app.metric[0].value != "30.01"
    # A loaded file cannot silently override the explicitly selected demo source.
    run(app, USER_CSV)
    assert app.button_group[0].value == "Демо-данные"
    app.button_group[0].set_value("Мой CSV")
    run(app)  # Hidden uploader state may be removed; the saved file survives.
    assert app.metric[0].value == "30.01"
    assert app.date_input[0].value == date(2026, 11, 1)
    assert any("Ваш CSV" in item.value for item in app.caption)


def test_switch_to_user_without_file_clears_demo_results():
    app = run(AppTest.from_file(APP))
    app.button_group[0].set_value("Мой CSV")
    run(app)
    assert not app.metric and not app.get("plotly_chart") and not app.date_input
    assert any("Загрузите файл" in item.value for item in app.caption)


def test_invalid_user_file_still_uses_existing_validation():
    app = run(AppTest.from_file(APP))
    app.button_group[0].set_value("Мой CSV")
    run(app, USER_CSV.replace(b"2026-11-01", b"2026-02-30"))
    assert app.error and "order_date" in app.error[0].value
    assert not app.metric and not app.get("plotly_chart")
