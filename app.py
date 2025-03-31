import streamlit as st
import pandas as pd

# Load data
df = pd.read_csv("test_final_with_predictions.csv")

st.set_page_config(page_title="NY SECURITIES", layout="wide")
st.title("📈 NY SECURITIES")
tabs = st.tabs(["STOCK RECOMMEND BY CANSLIM"])

with tabs[0]:
    st.header("STOCK RECOMMEND BY CANSLIM")

    # Select variables
    default_vars = ["Rate", "Predict"]
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    options = st.multiselect("Chọn biến để hiển thị và lọc:", options=numeric_cols, default=default_vars)

    filtered_df = df.copy()
    for var in options:
        if var in numeric_cols:
            min_val = float(filtered_df[var].min())
            max_val = float(filtered_df[var].max())
            selected_range = st.slider(f"Lọc theo {var}:", min_val, max_val, (min_val, max_val))
            filtered_df = filtered_df[(filtered_df[var] >= selected_range[0]) & (filtered_df[var] <= selected_range[1])]

    display_cols = ["Symbol"] + options + ["Predict"] if "Predict" not in options else ["Symbol"] + options
    st.markdown("### Dữ liệu đã lọc:")
    st.dataframe(filtered_df[display_cols].reset_index(drop=True), use_container_width=True)
