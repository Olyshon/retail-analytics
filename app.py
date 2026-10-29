import pandas as pd
import streamlit as st

from retail_analytics.metrics import calculate_metrics

st.set_page_config(page_title="Retail Analytics", page_icon="📊")

st.title("Retail Analytics")
st.write(
    "Учебное приложение для анализа продаж. Загрузите CSV, чтобы проверить "
    "его структуру, посмотреть первые строки и основные показатели."
)

REQUIRED_COLUMNS = (
    "order_id", "order_date", "product_name", "quantity", "unit_price"
)

st.caption("Формат: CSV в кодировке UTF-8, разделитель — запятая.")
st.caption("Обязательные столбцы: " + ", ".join(REQUIRED_COLUMNS))
uploaded_file = st.file_uploader("Загрузите CSV с продажами", type=["csv"])

if uploaded_file is not None:
    try:
        data = pd.read_csv(uploaded_file, encoding="utf-8-sig", dtype={"order_id": "string"})
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
                metrics = calculate_metrics(data)
            except ValueError as error:
                st.error(str(error))
            else:
                revenue_col, orders_col, average_col = st.columns(3)
                revenue_col.metric("Выручка", f"{metrics.revenue:,.2f}")
                orders_col.metric("Количество заказов", metrics.order_count)
                average_col.metric("Средний чек", f"{metrics.average_order_value:,.2f}")
            st.write(f"Общее количество строк: {len(data)}")
            st.subheader("Предварительный просмотр — первые 10 строк")
            st.dataframe(data.head(10), hide_index=True)
