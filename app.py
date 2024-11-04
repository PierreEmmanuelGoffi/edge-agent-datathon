__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from crew import create_crew

# Initialize session state
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
    st.session_state.stock_info = None
    st.session_state.stock_data = None
    st.session_state.result_file_path = None


def get_stock_data(stock_symbol, period="1y"):
    return yf.download(stock_symbol, period=period)


def plot_stock_chart(stock_data: pd.DataFrame, indicators: list) -> go.Figure:
    """
    Plot the stock data along with selected technical indicators.

    Args:
        stock_data (pd.DataFrame): The stock data to plot.
        indicators (list): A list of indicators to include in the plot (e.g., ['RSI', 'MACD']).

    Returns:
        go.Figure: The Plotly figure object.
    """
    # Flatten MultiIndex columns if present
    if isinstance(stock_data.columns, pd.MultiIndex):
        # Assuming the second level is the ticker symbol, drop it
        stock_data.columns = stock_data.columns.droplevel(1)

    # Create subplots: 3 rows (Price, Volume, RSI/MACD)
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("Price Chart", "Volume", "+".join(indicators)),
    )

    # Main price chart (Candlestick)
    fig.add_trace(
        go.Candlestick(
            x=stock_data.index,
            open=stock_data["Open"],
            high=stock_data["High"],
            low=stock_data["Low"],
            close=stock_data["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    # Add Moving Averages if selected
    if "Moving Averages" in indicators:
        # Calculate Moving Averages
        stock_data["50_MA"] = stock_data["Close"].rolling(window=50).mean()
        stock_data["200_MA"] = stock_data["Close"].rolling(window=200).mean()

        # Plot 50 MA
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=stock_data["50_MA"],
                name="50 MA",
                line=dict(color="orange"),
            ),
            row=1,
            col=1,
        )

        # Plot 200 MA
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=stock_data["200_MA"],
                name="200 MA",
                line=dict(color="red"),
            ),
            row=1,
            col=1,
        )

    # Add Volume if selected
    if "Volume" in indicators:
        fig.add_trace(
            go.Bar(
                x=stock_data.index,
                y=stock_data["Volume"],
                name="Volume",
                marker_color="blue",
            ),
            row=2,
            col=1,
        )

    # Add RSI if selected
    if "RSI" in indicators:
        delta = stock_data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        fig.add_trace(
            go.Scatter(
                x=stock_data.index, y=rsi, name="RSI", line=dict(color="purple")
            ),
            row=3,
            col=1,
        )

        # Add RSI overbought and oversold lines
        fig.add_hline(y=70, line=dict(color="red", dash="dash"), row=3, col=1)
        fig.add_hline(y=30, line=dict(color="green", dash="dash"), row=3, col=1)

    # Add MACD if selected
    if "MACD" in indicators:
        ema12 = stock_data["Close"].ewm(span=12, adjust=False).mean()
        ema26 = stock_data["Close"].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - signal

        fig.add_trace(
            go.Scatter(
                x=stock_data.index, y=macd, name="MACD", line=dict(color="blue")
            ),
            row=3,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=signal,
                name="Signal Line",
                line=dict(color="orange"),
            ),
            row=3,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=stock_data.index,
                y=macd_hist,
                name="MACD Histogram",
                marker_color="grey",
                opacity=0.5,
            ),
            row=3,
            col=1,
        )

    # Update layout
    fig.update_layout(
        title="Stock Analysis",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        template="seaborn",
    )

    # Update x-axes with range selectors
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all"),
                ]
            )
        ),
        rangeslider=dict(visible=False),
        type="date",
    )

    return fig


# Page configuration
st.set_page_config(
    layout="wide",
    page_title="Edge - Professional Stock Analysis",
    initial_sidebar_state="expanded",
)

# Custom CSS with modern design elements
st.markdown(
    """
<style>
    /* Main theme colors and variables */
    :root {
        --primary-color: #1E3A8A;
        --secondary-color: #3B82F6;
        --background-color: #F8FAFC;
        --card-background: #FFFFFF;
        --text-color: #1F2937;
    }

    /* Global styles */
    .stApp {
        background-color: var(--background-color);
    }

    .main {
        padding: 1rem;
    }

    /* Typography */
    .header-title {
        font-size: 2.5rem !important;
        font-weight: 800;
        color: var(--primary-color);
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .section-title {
        font-size: 1.5rem !important;
        font-weight: 700;
        color: var(--primary-color);
        margin: 1.5rem 0 1rem 0;
    }

    /* Cards */
    .info-card {
        background-color: var(--card-background);
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }

    .info-card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }

    .info-card-content {
        color: var(--text-color);
        line-height: 1.6;
    }

    /* Metrics */
    .metric-container {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1rem;
    }

    .metric-item {
        background-color: var(--card-background);
        border-radius: 8px;
        padding: 1rem;
        flex: 1;
        min-width: 200px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .metric-label {
        font-size: 0.9rem;
        color: #6B7280;
        margin-bottom: 0.25rem;
    }

    .metric-value {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--primary-color);
    }

    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: var(--card-background);
        padding: 1.5rem;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 1rem;
        color: #6B7280;
        font-size: 0.875rem;
    }

    /* Button styles */
    .stButton > button {
        width: 100%;
        background-color: var(--primary-color);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: background-color 0.3s;
    }

    .stButton > button:hover {
        background-color: var(--secondary-color);
    }

    /* Loading spinner */
    .stSpinner > div {
        border-top-color: var(--primary-color) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# App Header
st.markdown(
    '<h1 class="header-title">Professional Stock Analysis</h1>', unsafe_allow_html=True
)

# Sidebar Configuration
with st.sidebar:
    st.markdown(
        '<p class="section-title">Analysis Configuration</p>', unsafe_allow_html=True
    )

    with st.container():
        model_option = st.selectbox(
            "🤖 Select LLM Model",
            [
                "Claude Sonnet 3.0",
                "OpenAI GPT-4 Mini",
                "Llama 3 8B",
                "Llama 3.1 70B",
                "Llama 3.1 8B",
            ],
        )

        stock_symbol = st.text_input("📈 Stock Symbol", value="AAPL")

        time_period = st.selectbox(
            "⏱️ Time Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3
        )

        indicators = st.multiselect(
            "📊 Technical Indicators",
            ["Moving Averages", "Volume", "RSI", "MACD"],
            default=["Moving Averages", "Volume"],
        )

        analyze_button = st.button(
            "🔍 Analyze Stock",
            help="Click to start the stock analysis",
            use_container_width=True,
        )

# Initialize session state
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
    st.session_state.stock_info = None
    st.session_state.stock_data = None
    st.session_state.result_file_path = None

# Main content area
if analyze_button:
    st.session_state.analyzed = False

    with st.spinner("📊 Fetching market data..."):
        stock = yf.Ticker(stock_symbol)
        st.session_state.stock_info = stock.info
        st.session_state.stock_data = yf.download(stock_symbol, period=time_period)

    with st.spinner("🧠 Analyzing market patterns... (it can take up to 3 minutes"):
        st.session_state.result_file_path = create_crew(stock_symbol, model_option)

    st.session_state.analyzed = True

# Display stock information
if st.session_state.stock_info:
    st.markdown('<p class="section-title">Company Overview</p>', unsafe_allow_html=True)

    info = st.session_state.stock_info
    metrics = {
        "Current Price": f"${info.get('currentPrice', 'N/A'):,.2f}",
        "Market Cap": f"${info.get('marketCap', 0)/1e9:,.2f}B",
        "52-Week High": f"${info.get('fiftyTwoWeekHigh', 'N/A'):,.2f}",
        "52-Week Low": f"${info.get('fiftyTwoWeekLow', 'N/A'):,.2f}",
        "Volume": f"{info.get('volume', 0):,}",
        "P/E Ratio": f"{info.get('trailingPE', 'N/A'):,.2f}",
    }

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""<div class="info-card">
                <div class="info-card-title">Company Profile</div>
                <div class="info-card-content">
                    <strong>Name:</strong> {info.get('longName', 'N/A')}<br>
                    <strong>Sector:</strong> {info.get('sector', 'N/A')}<br>
                    <strong>Industry:</strong> {info.get('industry', 'N/A')}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""<div class="info-card">
                <div class="info-card-title">Financial Metrics</div>
                <div class="info-card-content">
                    <strong>Revenue:</strong> ${info.get('totalRevenue', 0)/1e9:,.2f}B<br>
                    <strong>Gross Profit:</strong> ${info.get('grossProfits', 0)/1e9:,.2f}B<br>
                    <strong>Operating Margin:</strong> {info.get('operatingMargins', 0)*100:.2f}%
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""<div class="info-card">
                <div class="info-card-title">Trading Information</div>
                <div class="info-card-content">
                    <strong>Exchange:</strong> {info.get('exchange', 'N/A')}<br>
                    <strong>Currency:</strong> {info.get('currency', 'N/A')}<br>
                    <strong>Average Volume:</strong> {info.get('averageVolume', 0):,}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    # Display metrics in a grid
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    for label, value in metrics.items():
        st.markdown(
            f"""<div class="metric-item">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

# Display analysis results
if st.session_state.result_file_path:
    st.markdown('<p class="section-title">AI Analysis</p>', unsafe_allow_html=True)

    with open(st.session_state.result_file_path, "r") as file:
        result = file.read()

    st.markdown(
        f"""<div class="info-card">
            <div class="info-card-content">{result}</div>
        </div>""",
        unsafe_allow_html=True,
    )

# Display interactive chart
if st.session_state.analyzed and st.session_state.stock_data is not None:
    st.markdown(
        '<p class="section-title">Technical Analysis</p>', unsafe_allow_html=True
    )

    # Create and display the chart using the existing plot_stock_chart function
    fig = plot_stock_chart(st.session_state.stock_data, indicators)
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown(
    """
<div class="footer">
    <p>Data provided by Yahoo Finance | Last updated: {}</p>
</div>
""".format(
        pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    ),
    unsafe_allow_html=True,
)
