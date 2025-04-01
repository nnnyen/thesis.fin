import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from vnstock import Vnstock
from bs4 import BeautifulSoup
import urllib3

# === Setup ===
st.set_page_config(page_title="NY SECURITIES", layout="wide")
http = urllib3.PoolManager()

# === Load Data ===
company_df = pd.read_excel("company_list.xlsx")
company_df.columns = company_df.columns.str.strip()

# === Function: Get News ===
def get_news(symbol):
    try:
        url = f"http://s.cafef.vn/Ajax/Events_RelatedNews_New.aspx?symbol={symbol}&floorID=0&configID=0&PageIndex=1&PageSize=10000&Type=2"
        response = http.request('GET', url)
        soup = BeautifulSoup(response.data, "html.parser")
        news_items = soup.find("ul", {"class": "News_Title_Link"}).find_all('li')
        return pd.DataFrame([{
            "newsdate": li.span.text,
            "title": li.a.text,
            "url": "http://s.cafef.vn/" + li.a['href']
        } for li in news_items])
    except:
        return pd.DataFrame([])

# === Layout ===
tabs = st.tabs(["Biểu đồ giá", "STOCK RECOMMEND BY CANSLIM"])

# === Tab 1: Biểu đồ giá ===
with tabs[0]:
    st.title("\U0001F4C8 BIểU ĐỒ GIÁ")

    col1, col2 = st.columns([2, 2])
    with col1:
        default_symbol = "VNM"
        symbol = st.selectbox("Chọn mã cổ phiếu:", company_df["symbol"].unique(), index=company_df["symbol"].tolist().index(default_symbol))
    with col2:
        indicators = st.multiselect("Chọn chỉ báo kỹ thuật:", ["SMA 10/20", "RSI", "MACD", "Bollinger Bands"])

    stock = Vnstock().stock(symbol=symbol, source='TCBS')
    hist_df = stock.quote.history(symbol=symbol, start="2022-01-01", end="2025-01-01", interval="1D")
    hist_df['time'] = pd.to_datetime(hist_df['time'])

    fig = go.Figure(data=[go.Candlestick(
        x=hist_df['time'], open=hist_df['open'], high=hist_df['high'],
        low=hist_df['low'], close=hist_df['close']
    )])

    if "SMA 10/20" in indicators:
        hist_df['SMA10'] = hist_df['close'].rolling(10).mean()
        hist_df['SMA20'] = hist_df['close'].rolling(20).mean()
        fig.add_trace(go.Scatter(x=hist_df['time'], y=hist_df['SMA10'], mode='lines', name='SMA 10'))
        fig.add_trace(go.Scatter(x=hist_df['time'], y=hist_df['SMA20'], mode='lines', name='SMA 20'))

    fig.update_layout(title=f"Biểu đồ giá cổ phiếu {symbol}", xaxis_title="Thời gian", yaxis_title="Giá")
    chart_col, info_col = st.columns([3, 1])

    with chart_col:
        st.plotly_chart(fig, use_container_width=True)

    with info_col:
        info = company_df[company_df.symbol == symbol].iloc[0]
        st.subheader(":information_source: Thông tin doanh nghiệp")
        st.write(f"**Tên:** {info['Company Common Name']}")
        st.write(f"**Ngành:** {info['GICS Industry Name']}")
        st.write(f"**Năm thành lập:** {info['Organization Founded Year']}")

        news = get_news(symbol)
        st.subheader(":newspaper: Tin tức liên quan")
        for _, row in news.head(5).iterrows():
            st.markdown(f"[{row['newsdate']} - {row['title']}]({row['url']})")

    st.subheader(":scroll: Giao dịch realtime")
    try:
        realtime_df = stock.quote.intraday(symbol=symbol)
        st.dataframe(realtime_df, use_container_width=True)
    except:
        st.warning("Không tải được dữ liệu realtime")

# === Tab 2: CANSLIM ===
with tabs[1]:
    st.header("STOCK RECOMMEND BY CANSLIM")
    df = pd.read_csv("test_final_with_predictions.csv")
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    default_cols = ["Symbol", "Rate", "Pivot Price (Buy)", "Target Price (Sell)", "Stop Loss Price", "Predict"]
    numeric_cols = df.select_dtypes(include='number').columns.tolist()

    left, right = st.columns([1, 2])
    with left:
        filters = st.multiselect(":pencil: Chọn các biến để lọc:", numeric_cols, default=["Rate"])
    with right:
        filtered_df = df.copy()
        for f in filters:
            min_val = float(df[f].min())
            max_val = float(df[f].max())
            selected = st.slider(f, min_val, max_val, (min_val, max_val), key=f)
            filtered_df = filtered_df[(filtered_df[f] >= selected[0]) & (filtered_df[f] <= selected[1])]

    st.markdown("### Dữ liệu sau khi lọc:")
    st.dataframe(
        filtered_df[default_cols].sort_values("Rate", ascending=False).reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

# === CSS xanh lá ===
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
