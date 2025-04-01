import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    st.title("\U0001F4C8 BIỂU ĐỒ GIÁ")

    col1, col2 = st.columns([2, 2])
    with col1:
        default_symbol = "VNM"
        symbol = st.selectbox("Chọn mã cổ phiếu:", company_df["symbol"].unique(), index=company_df["symbol"].tolist().index(default_symbol))
    with col2:
        indicators = st.multiselect("Chọn chỉ báo kỹ thuật:", ["SMA 10/20", "RSI", "MACD", "Bollinger Bands", "Stochastic Oscillator"])
        apply = st.button("Áp dụng")

    stock = Vnstock().stock(symbol=symbol, source='TCBS')
    hist_df = stock.quote.history(symbol=symbol, start="2022-01-01", end="2025-01-01", interval="1D")
    hist_df['time'] = pd.to_datetime(hist_df['time'])
    hist_df = hist_df.drop_duplicates(subset='time')
    hist_df = hist_df.set_index('time').asfreq('D').ffill().reset_index()

    rows = 1
    row_heights = [1.0]
    if apply and any(ind in indicators for ind in ["RSI", "MACD", "Stochastic Oscillator"]):
        rows += 1
        row_heights = [0.7, 0.3]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=row_heights,
        specs=[[{"type": "candlestick"}]] + [[{"type": "xy"}]] * (rows - 1)
    )

    fig.add_trace(go.Candlestick(
        x=hist_df['time'], open=hist_df['open'], high=hist_df['high'],
        low=hist_df['low'], close=hist_df['close'], name="Giá"
    ), row=1, col=1)

    indicator_row = 2 if rows > 1 else 1

    if apply:
        if "SMA 10/20" in indicators:
            hist_df['SMA10'] = hist_df['close'].rolling(10).mean()
            hist_df['SMA20'] = hist_df['close'].rolling(20).mean()
            fig.add_trace(go.Scatter(x=hist_df['time'], y=hist_df['SMA10'], mode='lines', name='SMA 10'), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist_df['time'], y=hist_df['SMA20'], mode='lines', name='SMA 20'), row=1, col=1)
        if "RSI" in indicators:
            delta = hist_df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            fig.add_trace(go.Scatter(x=hist_df['time'], y=rsi, mode='lines', name='RSI'), row=indicator_row, col=1)
        if "MACD" in indicators:
            exp1 = hist_df['close'].ewm(span=12, adjust=False).mean()
            exp2 = hist_df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal
            fig.add_trace(go.Bar(x=hist_df['time'], y=hist, name='Histogram', marker_color='pink'), row=indicator_row, col=1)
            fig.add_trace(go.Scatter(x=hist_df['time'], y=macd, mode='lines', name='MACD', line=dict(color='blue')), row=indicator_row, col=1)
            fig.add_trace(go.Scatter(x=hist_df['time'], y=signal, mode='lines', name='Signal', line=dict(color='red')), row=indicator_row, col=1)
        if "Bollinger Bands" in indicators:
            sma = hist_df['close'].rolling(window=20).mean()
            std = hist_df['close'].rolling(window=20).std()
            upper_band = sma + (2 * std)
            lower_band = sma - (2 * std)
            fig.add_trace(go.Scatter(x=hist_df['time'], y=upper_band, mode='lines', name='Upper Band'), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist_df['time'], y=lower_band, mode='lines', name='Lower Band'), row=1, col=1)
        if "Stochastic Oscillator" in indicators:
            low_min = hist_df['low'].rolling(window=14).min()
            high_max = hist_df['high'].rolling(window=14).max()
            k_percent = 100 * ((hist_df['close'] - low_min) / (high_max - low_min))
            d_percent = k_percent.rolling(3).mean()
            fig.add_trace(go.Scatter(x=hist_df['time'], y=k_percent, mode='lines', name='%K'), row=indicator_row, col=1)
            fig.add_trace(go.Scatter(x=hist_df['time'], y=d_percent, mode='lines', name='%D'), row=indicator_row, col=1)

    start_date = pd.to_datetime(hist_df['time'].max() - pd.Timedelta(days=365))
    end_date = pd.to_datetime(hist_df['time'].max())

    fig.update_layout(
        height=850,
        title=f"Biểu đồ giá cổ phiếu {symbol}",
        xaxis_rangeslider_visible=not apply,
        xaxis_range=[start_date, end_date],
        hovermode="x unified",
        xaxis_showspikes=True,
        xaxis_spikemode='across',
        xaxis_spikesnap='cursor',
        xaxis_spikethickness=1,
        xaxis_spikedash='dot',
        xaxis_spikecolor='black',
        showlegend=True,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    chart_col, info_col = st.columns([7, 2])

    with chart_col:
        st.plotly_chart(fig, use_container_width=True)

    with info_col:
        info = company_df[company_df.symbol == symbol].iloc[0]
        st.subheader(":information_source: Thông tin doanh nghiệp")
        st.write(f"**Tên:** {info['Company Common Name']}")
        st.write(f"**Ngành:** {info['GICS Industry Name']}")
        st.write(f"**Năm thành lập:** {info['Organization Founded Year']}")
        st.write(f"**Sàn:** {info['Exchange Name']}")

        news = get_news(symbol)
        st.subheader(":newspaper: Tin tức liên quan")
        for _, row in news.head(5).iterrows():
            st.markdown(f"[{row['newsdate']} - {row['title']}]({row['url']})")

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
# === Tab 3: Finacial health===
with tabs[2]:
    st.title(":bar_chart: Financial Ratio")
    df = pd.read_csv("df.csv")
    industry_col = "GICS Industry Name"
    df = df.merge(company_df[['symbol', industry_col]], left_on="Ticker", right_on="symbol", how="left")

    columns = ["CR(X1)", "QR(X2)", "DR(X3)", "TA(X4)", "IT(X5))", "PM(X6))", "ROA(X7))", "ROE(X8)", "BEP(X9))", "NWC(X10))", "RE(X11)", "MVE(X12)"]
    selected_cols = st.multiselect("Chọn các biến:", columns, default=["CR(X1)", "DR(X3)", "TA(X4)", "PM(X6))", "NWC(X10))"])

    if selected_cols:
        st.write("### Trung bình ngành")
        industry_means = df.groupby(industry_col)[selected_cols].mean().rename_axis("Ngành")
        st.dataframe(industry_means)

        st.write("### Các mã có giá trị cao hơn trung bình ngành")
        rows = []
        for _, row in df.iterrows():
            industry = row[industry_col]
            keep = True
            for col in selected_cols:
                if pd.isna(row[col]) or row[col] <= industry_means.loc[industry, col]:
                    keep = False
                    break
            if keep:
                rows.append(row)

        filtered_df = pd.DataFrame(rows)
        st.dataframe(filtered_df[["Ticker"] + selected_cols + [industry_col]])

        st.write("### Dữ liệu của quý gần nhất")
        if "Period Ending" in df.columns:
            latest_quarter = df["Period Ending"].max()
            st.write(f"#### Quý gần nhất: {latest_quarter}")
            latest_df = filtered_df[filtered_df["Period Ending"] == latest_quarter]
            st.dataframe(latest_df[["Ticker"] + selected_cols + [industry_col, "Period Ending"]])
            st.download_button(
                label="📥 Tải xuống CSV",
                data=latest_df.to_csv(index=False),
                file_name=f"financial_ratio_latest_quarter.csv",
                mime="text/csv"
            )
        else:
            st.warning("Không tìm thấy cột 'Period Ending' để lọc quý gần nhất.")

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
