import streamlit as st
import pandas as pd

# Load data
df = pd.read_csv("test_final_with_predictions.csv")

# Remove unnecessary columns like 'Unnamed: 0'
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]  # removes Unnamed columns if any

st.set_page_config(page_title="NY SECURITIES", layout="wide")

# --- TITLE & TABS ---
st.title("📈 NY SECURITIES")
tabs = st.tabs(["STOCK RECOMMEND BY CANSLIM"])

with tabs[0]:
    st.header("STOCK RECOMMEND BY CANSLIM")

    # --- DEFAULT & FILTER SETUP ---
    default_display = ["Symbol", "Rate", "Pivot Price (Buy)", "Target Price (Sell)", "Stop Loss Price", "Predict"]
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    available_vars = [col for col in numeric_cols if col not in ["Symbol"]]

    col1, col2 = st.columns([1, 2])

    with col1:
        selected_vars = st.multiselect("\U0001F4DD Chọn biến để lọc:", options=available_vars, default=["Rate"])

    with col2:
        filtered_df = df.copy()
        if selected_vars:
            sliders = []
            for var in selected_vars:
                if var in numeric_cols:
                    min_val = float(filtered_df[var].min())
                    max_val = float(filtered_df[var].max())
                    selected_range = st.slider(
                        f"{var}",
                        min_val, max_val, (min_val, max_val),
                        key=var,
                        label_visibility="visible"
                    )
                    filtered_df = filtered_df[(filtered_df[var] >= selected_range[0]) & (filtered_df[var] <= selected_range[1])]

    # --- DISPLAY TABLE ---
    display_cols = [col for col in default_display if col in filtered_df.columns]
    st.markdown("### Dữ liệu đã lọc:")
    st.dataframe(
        filtered_df[display_cols].sort_values(by="Rate", ascending=False).reset_index(drop=True), 
        use_container_width=True,
        hide_index=True
    )

    # --- CUSTOM CSS ---
    st.markdown("""
        <style>
        div[data-baseweb="slider"] [role="slider"] {
            background-color: #28a745 !important;
            border: 1px solid #28a745 !important;
        }
        div[data-baseweb="slider"] > div > div {
            background: #28a74533 !important;
        }
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #28a745 !important;
            color: white !important;
        }
        .stMultiSelect [data-baseweb="select"] > div {
            border-color: #28a745 !important;
        }
        </style>
    """, unsafe_allow_html=True)
