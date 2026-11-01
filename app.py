from hashlib import sha256

import pandas as pd
import streamlit as st

from retail_analytics.charts import revenue_chart, top_products_chart
from retail_analytics.csv_loader import load_sales_csv
from retail_analytics.filters import filter_by_date
from retail_analytics.metrics import calculate_metrics, daily_revenue, top_products

st.set_page_config(page_title="Retail Analytics", page_icon="📊")

st.title("Retail Analytics")
st.write(
    "Учебное приложение для анализа продаж. Загрузите CSV, чтобы проверить "
    "его структуру, посмотреть первые строки, основные показатели и динамику выручки."
)

REQUIRED_COLUMNS = (
    "order_id", "order_date", "product_name", "quantity", "unit_price"
)

st.caption("Формат: CSV в кодировке UTF-8, разделитель — запятая.")
st.caption("Обязательные столбцы: " + ", ".join(REQUIRED_COLUMNS))
uploaded_file = st.file_uploader("Загрузите CSV с продажами", type=["csv"])

if uploaded_file is not None:
    try:
        data = load_sales_csv(uploaded_file)
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
                file_key = sha256(uploaded_file.getvalue()).hexdigest()
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
                revenue_col, orders_col, average_col = st.columns(3)
                revenue_col.metric("Выручка", f"{metrics.revenue:,.2f}")
                orders_col.metric("Количество заказов", metrics.order_count)
                average_col.metric("Средний чек", f"{metrics.average_order_value:,.2f}")
                if filtered.empty:
                    st.info("В выбранном периоде нет продаж. Выберите другой диапазон дат.")
                else:
                    st.subheader("Динамика выручки по дням")
                    st.plotly_chart(revenue_chart(daily_revenue(filtered)), width="stretch")
                    st.caption("Показаны даты с записями о продажах. Дни без записей не добавляются.")
                    st.subheader("Топ-10 товаров по выручке")
                    st.plotly_chart(top_products_chart(top_products(filtered)), width="stretch")
                st.write(f"Количество строк в выбранном периоде: {len(filtered)}")
                st.subheader("Предварительный просмотр — первые 10 строк периода")
                st.dataframe(filtered.head(10), hide_index=True)
