from hashlib import sha256
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from retail_analytics.charts import revenue_chart, top_products_chart
from retail_analytics.csv_loader import load_sales_csv
from retail_analytics.filters import filter_by_date
from retail_analytics.metrics import calculate_metrics, daily_revenue, top_products

st.set_page_config(page_title="Retail Analytics", page_icon="📊", layout="wide")

# Только собственные ключи контейнеров: без селекторов внутренней разметки Streamlit.
st.html("""<style>
.st-key-controls, .st-key-daily_panel, .st-key-products_panel, .st-key-preview_panel {
    background: #ffffff;
}
</style>""")

st.title("Retail Analytics")
st.caption("Панель анализа продаж")

REQUIRED_COLUMNS = (
    "order_id", "order_date", "product_name", "quantity", "unit_price"
)

DEMO_SOURCE = "Демо-данные"
USER_SOURCE = "Мой CSV"


def remember_upload():
    uploaded = st.session_state.get("user_upload")
    st.session_state["saved_upload"] = (
        (uploaded.getvalue(), uploaded.name) if uploaded is not None else None
    )


try:
    sample_bytes = (Path(__file__).resolve().parent / "data" / "sample_sales.csv").read_bytes()
except OSError:
    sample_bytes = None

controls = st.container(border=True, key="controls")
with controls:
    source = st.segmented_control(
        "Источник данных", [DEMO_SOURCE, USER_SOURCE], default=DEMO_SOURCE,
        required=True, key="source_mode", label_visibility="collapsed",
    )

with controls:
    source_bytes = None
    if source == DEMO_SOURCE:
        if sample_bytes is None:
            st.error("Демонстрационный файл недоступен. Загрузите свой CSV или проверьте data/sample_sales.csv.")
        else:
            source_bytes = sample_bytes
            with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"):
                st.caption("Синтетические продажи · sample_sales.csv")
                st.download_button(
                    "Скачать CSV", data=sample_bytes, file_name="sample_sales.csv",
                    mime="text/csv", on_click="ignore",
                )
    else:
        st.caption("CSV · UTF-8 · разделитель — запятая")
        st.caption("Обязательные столбцы: " + ", ".join(REQUIRED_COLUMNS))
        uploaded_file = st.file_uploader(
            "Загрузите CSV с продажами", type=["csv"], key="user_upload",
            on_change=remember_upload,
        )
        if uploaded_file is not None:
            st.session_state["saved_upload"] = (
                uploaded_file.getvalue(), getattr(uploaded_file, "name", "загруженный файл")
            )
        saved_upload = st.session_state.get("saved_upload")
        if saved_upload is not None:
            source_bytes, filename = saved_upload
            st.caption(f"Ваш CSV · {filename}")
        else:
            st.caption("Загрузите файл для анализа.")

if source_bytes is not None:
    try:
        data = load_sales_csv(BytesIO(source_bytes))
    except pd.errors.EmptyDataError:
        st.error("Файл пустой: добавьте заголовки столбцов и строки с продажами.")
    except (pd.errors.ParserError, UnicodeDecodeError, OSError, ValueError):
        st.error(
            "Не удалось прочитать CSV. Проверьте структуру файла, "
            "кодировку UTF-8 и разделитель — запятую."
        )
    else:
        missing_columns = [name for name in REQUIRED_COLUMNS if name not in data.columns]
        if missing_columns:
            st.error("Не хватает обязательных столбцов: " + ", ".join(missing_columns))
        elif data.empty:
            st.warning("В файле есть заголовки, но нет строк с продажами.")
        else:
            try:
                calculate_metrics(data)  # Проверяем весь файл до выбора периода.
            except ValueError as error:
                st.error(str(error))
                st.write(f"Общее количество строк: {len(data)}")
                st.subheader("Предварительный просмотр — первые 10 строк")
                st.dataframe(data.head(10), hide_index=True)
            else:
                dates = pd.to_datetime(data["order_date"], format="%Y-%m-%d")
                min_date, max_date = dates.min().date(), dates.max().date()
                # Новый файл получает весь диапазон, повторный запуск сохраняет выбор.
                file_key = sha256(source.encode("utf-8") + source_bytes).hexdigest()
                with controls:
                    start_col, end_col = st.columns(2)
                    start_date = start_col.date_input(
                        "Начальная дата", value=min_date, min_value=min_date,
                        max_value=max_date, key=f"start_{file_key}",
                    )
                    end_date = end_col.date_input(
                        "Конечная дата", value=max_date, min_value=min_date,
                        max_value=max_date, key=f"end_{file_key}",
                    )
                try:
                    filtered = filter_by_date(data, start_date, end_date)
                except ValueError as error:
                    st.error(str(error))
                    st.stop()

                metrics = calculate_metrics(filtered)
                revenue_col, orders_col, average_col = st.columns(3, border=True, gap="medium")
                revenue_col.metric(":gray[Выручка]", f"{metrics.revenue:,.2f}")
                orders_col.metric(":gray[Количество заказов]", metrics.order_count)
                average_col.metric(":gray[Средний чек]", f"{metrics.average_order_value:,.2f}")
                if filtered.empty:
                    st.info("В выбранном периоде нет продаж. Выберите другой диапазон дат.")
                else:
                    with st.container(border=True, key="daily_panel"):
                        st.subheader("Динамика выручки по дням")
                        st.plotly_chart(revenue_chart(daily_revenue(filtered)), width="stretch", theme=None)
                        st.caption("Показаны даты с записями о продажах. Дни без записей не добавляются.")
                    with st.container(border=True, key="products_panel"):
                        st.subheader("Топ-10 товаров по выручке")
                        st.plotly_chart(top_products_chart(top_products(filtered)), width="stretch", theme=None)
                with st.container(border=True, key="preview_panel"):
                    st.write(f"Количество строк в выбранном периоде: {len(filtered)}")
                    st.subheader("Предварительный просмотр — первые 10 строк периода")
                    st.dataframe(filtered.head(10), hide_index=True)
