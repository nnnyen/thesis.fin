import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from vnstock import Vnstock
from bs4 import BeautifulSoup
import urllib3

# Setup HTTP pool for news scraping
http = urllib3.PoolManager()

# Load company info
company_df = pd.read_excel("company_list.xlsx")
company_df.columns = company_df.columns.str.strip()

# --- Set Streamlit Page ---
st.set_page_config(page_title="NY SECURITIES", layout="wide")

# --- Define function to get news ---
def get_new_data(symbol):
    try:
        r = http.request('GET', f'http://s.cafef.vn/Ajax/Events_RelatedNews_New.aspx?symbol={symbol}&floorID=0&configID=0&PageIndex=1&PageSize=10000&Type=2')
        soup = BeautifulSoup(r.data, "html.parser")
        data = soup.find("ul", {"class": "News_Title_Link"})
        raw = data.find_all('li')
        data_dicts = []
        for row in raw:
            row_dict = {
                'newsdate': row.span.text,
                'title': row.a.text,
                'url': "http://s.cafef.vn/" + str(row.a['href']),
                'ticker': symbol
            }
            data_dicts.append(row_dict)
        return pd.DataFrame(data_dicts)
    except:
        return pd.DataFrame([])

# --- Define tab layout ---
tabs = st.tabs(["Biểu đồ giá", "STOCK RECOMMEND BY CANSLIM"])

# --- Tab 1: Price Chart ---
with tabs[0]:
    st.title("📊 BIỂU ĐỒ GIÁ")
    
    col1, col2 = st.columns([2, 2])
    with col1:
        symbol = st.selectbox("Chọn mã cổ phiếu:", company_df["ticker"].unique(), index=company_df["ticker"].tolist().index("VNM"))
    with col2:
        indicators = st.multiselect("Chọn chỉ báo kỹ thuật:", ["SMA 10/20", "RSI", "MACD", "Bollinger Bands"])

    # Load historical price data
    stock = Vnstock().stock(symbol=symbol, source='TCBS')
    hist_df = stock.quote.history(symbol=symbol, start="2022-01-01", end="2025-01-01", interval="1D")
    hist_df['time'] = pd.to_datetime(hist_df['time'])

    # Candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=hist_df['time'],
        open=hist_df['open'],
        high=hist_df['high'],
        low=hist_df['low'],
        close=hist_df['close']
    )])

    # Add indicators (placeholders)
    if "SMA 10/20" in indicators:
        hist_df['SMA10'] = hist_df['close'].rolling(10).mean()
        hist_df['SMA20'] = hist_df['close'].rolling(20).mean()
        fig.add_trace(go.Scatter(x=hist_df['time'], y=hist_df['SMA10'], mode='lines', name='SMA 10'))
        fig.add_trace(go.Scatter(x=hist_df['time'], y=hist_df['SMA20'], mode='lines', name='SMA 20'))

    fig.update_layout(title=f"Biểu đồ giá cổ phiếu {symbol}", xaxis_title="Thời gian", yaxis_title="Giá", height=500)

    col_chart, col_info = st.columns([3, 1])
    with col_chart:
        st.plotly_chart(fig, use_container_width=True)

    with col_info:
        info_row = company_df[company_df["ticker"] == symbol].iloc[0]
        st.subheader("📘 Thông tin doanh nghiệp")
        st.write(f"**Tên công ty**: {info_row['name']}\n\n**Ngành**: {info_row['industry']}\n\n**Thành lập**: {info_row['founding']}")

        news_df = get_new_data(symbol)
        st.subheader("📰 Tin tức liên quan")
        for _, row in news_df.head(5).iterrows():
            st.markdown(f"[{row['newsdate']} - {row['title']}]({row['url']})")

    # Transaction data
    st.subheader("📑 Bảng giao dịch (Realtime)")
    try:
        live_df = stock.quote.intraday(symbol=symbol)
        st.dataframe(live_df, use_container_width=True)
    except:
        st.warning("Không thể tải dữ liệu giao dịch.")


# --- Tab 2: STOCK RECOMMEND BY CANSLIM ---
with tabs[1]:
    st.header("STOCK RECOMMEND BY CANSLIM")

    df = pd.read_csv("test_final_with_predictions.csv")
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    default_display = ["Symbol", "Rate", "Pivot Price (Buy)", "Target Price (Sell)", "Stop Loss Price", "Predict"]
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    available_vars = [col for col in numeric_cols if col not in ["Symbol"]]

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_vars = st.multiselect("\U0001F4DD Chọn biến để lọc:", options=available_vars, default=["Rate"])

    with col2:
        filtered_df = df.copy()
        if selected_vars:
            for var in selected_vars:
                if var in numeric_cols:
                    min_val = float(filtered_df[var].min())
                    max_val = float(filtered_df[var].max())
                    selected_range = st.slider(
                        f"{var}", min_val, max_val, (min_val, max_val),
                        key=var, label_visibility="visible"
                    )
                    filtered_df = filtered_df[(filtered_df[var] >= selected_range[0]) & (filtered_df[var] <= selected_range[1])]

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
