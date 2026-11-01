from datetime import date
from io import BytesIO
from pathlib import Path
import json
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


CSV = (
    "order_id,order_date,product_name,quantity,unit_price\n"
    "1,2026-10-01,Coffee,1,10\n"
    "2,2026-10-03,Tea,2,20\n"
    "2,2026-10-03,Cookie,1,5\n"
    "3,2026-10-05,Coffee,3,10\n"
).encode()
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def run_app(app, payload=CSV):
    app.session_state["source_mode"] = "Мой CSV"
    with patch("streamlit.file_uploader", return_value=BytesIO(payload)):
        app.run(timeout=30)
    assert not app.exception
    return app


def test_filter_controls_metrics_chart_and_preview():
    app = run_app(AppTest.from_file(APP_PATH))
    assert [field.value for field in app.date_input] == [date(2026, 10, 1), date(2026, 10, 5)]
    assert [metric.value for metric in app.metric] == ["85.00", "3", "28.33"]
    assert len(app.dataframe[0].value) == 4

    app.date_input[0].set_value(date(2026, 10, 3))
    app.date_input[1].set_value(date(2026, 10, 3))
    run_app(app)
    assert [metric.value for metric in app.metric] == ["45.00", "1", "45.00"]
    assert len(app.get("plotly_chart")) == 2
    ranking = json.loads(app.get("plotly_chart")[1].proto.spec)
    assert ranking["data"][0]["y"] == ["Tea", "Cookie"]
    assert ranking["data"][0]["customdata"] == [["40.00"], ["5.00"]]
    assert app.dataframe[0].value["order_date"].tolist() == ["2026-10-03"] * 2

    app.date_input[0].set_value(date(2026, 10, 2))
    app.date_input[1].set_value(date(2026, 10, 2))
    run_app(app)
    assert [metric.value for metric in app.metric] == ["0.00", "0", "0.00"]
    assert not app.get("plotly_chart")
    assert any("нет продаж" in message.value for message in app.info)
    assert app.dataframe[0].value.empty


def test_reversed_range_does_not_show_stale_results():
    app = run_app(AppTest.from_file(APP_PATH))
    app.date_input[0].set_value(date(2026, 10, 5))
    app.date_input[1].set_value(date(2026, 10, 1))
    run_app(app)
    assert "Начальная дата" in app.error[0].value
    assert not app.metric and not app.get("plotly_chart") and not app.dataframe


def test_new_file_resets_range_and_invalid_file_has_no_filter():
    app = run_app(AppTest.from_file(APP_PATH))
    app.date_input[0].set_value(date(2026, 10, 3))
    run_app(app)
    new_csv = CSV.replace(b"2026-10-", b"2026-11-")
    run_app(app, new_csv)
    assert [field.value for field in app.date_input] == [date(2026, 11, 1), date(2026, 11, 5)]
    run_app(app, CSV.replace(b"2026-10-01", b"2026-02-30"))
    assert app.error
    assert not app.date_input and not app.metric and not app.get("plotly_chart")
