import streamlit as st
import pandas as pd

# Load data (replace with GitHub/raw URL or local file path in actual deployment)
df = pd.read_csv("test_final_with_predictions.csv")

st.set_page_config(page_title="NY SECURITIES", layout="wide")

# --- TITLE & TABS ---
st.title("📈 NY SECURITIES")
tabs = st.tabs(["STOCK RECOMMEND BY CANSLIM"])

with tabs[0]:
    st.header("STOCK RECOMMEND BY CANSLIM")

    # --- VARIABLE SELECTION ---
    all_numeric_cols = df.select_dtypes(include='number').columns.tolist()
    default_vars = [col for col in ["Rate", "Predict"] if col in all_numeric_cols]

    options = st.multiselect("Chọn biến để hiển thị và lọc:", options=all_numeric_cols, default=default_vars)

    # --- FILTER RANGE SLIDER ---
    filtered_df = df.copy()
    for var in options:
        if var in all_numeric_cols:
            min_val = float(filtered_df[var].min())
            max_val = float(filtered_df[var].max())
            selected_range = st.slider(f"Lọc theo {var}:", min_val, max_val, (min_val, max_val))
            filtered_df = filtered_df[(filtered_df[var] >= selected_range[0]) & (filtered_df[var] <= selected_range[1])]

    # --- DISPLAY TABLE ---
    extra_cols = ["Predict"] if "Predict" not in options and "Predict" in df.columns else []
    display_cols = ["Symbol"] + options + extra_cols

    st.markdown("### Dữ liệu đã lọc:")
    st.dataframe(filtered_df[display_cols].reset_index(drop=True), use_container_width=True)

