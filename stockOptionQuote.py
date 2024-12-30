import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import streamlit as st

# Default settings
DEFAULT_SETTINGS = {
    "stock_ticker": "AAPL",
    "input_date_str": dt.datetime.now().strftime("%Y-%m-%d"),
    "put_range": (-20, 5),
    "call_range": (-5, 20),
    "plot_put": True,
    "plot_call": False
}

# Initialize session state if not already set
if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULT_SETTINGS.copy()

# Load defaults on button click
if st.button("Load Defaults"):
    st.session_state.inputs = DEFAULT_SETTINGS.copy()

# Input fields
st.markdown("<h1 style='text-align: center; font-size: 48px;'>Options Quote Visualizer</h1>", unsafe_allow_html=True)

stock_ticker = st.text_input(
    "Enter stock ticker:",
    st.session_state.inputs["stock_ticker"]
)
st.session_state.inputs["stock_ticker"] = stock_ticker

input_date_str = st.date_input(
    "Enter date:",
    pd.to_datetime(st.session_state.inputs["input_date_str"])
)
st.session_state.inputs["input_date_str"] = input_date_str.strftime("%Y-%m-%d")

put_range = st.slider(
    "Put Range (as % of stock price):",
    -50, 10, st.session_state.inputs["put_range"]
)
st.session_state.inputs["put_range"] = put_range

call_range = st.slider(
    "Call Range (as % of stock price):",
    -10, 50, st.session_state.inputs["call_range"]
)
st.session_state.inputs["call_range"] = call_range

plot_put = st.checkbox(
    "Plot Puts",
    value=st.session_state.inputs["plot_put"]
)
st.session_state.inputs["plot_put"] = plot_put

plot_call = st.checkbox(
    "Plot Calls",
    value=st.session_state.inputs["plot_call"]
)
st.session_state.inputs["plot_call"] = plot_call

# Fetch stock data
try:
    stock = yf.Ticker(stock_ticker)
    expiration_dates = stock.options
    input_date = dt.datetime.strptime(st.session_state.inputs["input_date_str"], "%Y-%m-%d")
    next_friday = input_date + dt.timedelta((4 - input_date.weekday()) % 7)
    next_friday_str = next_friday.strftime('%Y-%m-%d')

    if next_friday_str not in expiration_dates:
        st.error(f"No options data available for {next_friday_str}. Try another date.")
    else:
        calls = stock.option_chain(next_friday_str).calls
        puts = stock.option_chain(next_friday_str).puts
        stock_price = stock.history(period="1d")['Close'].iloc[-1]

        def process_option_data(option_data, stock_price):
            option_data = option_data.copy()
            option_data["incremental_percentage"] = (option_data["strike"] - stock_price) / stock_price * 100
            option_data["bid_ratio"] = option_data["bid"] / option_data["strike"] * 100
            option_data["ask_ratio"] = option_data["ask"] / option_data["strike"] * 100
            return option_data

        calls_processed = process_option_data(calls, stock_price)
        puts_processed = process_option_data(puts, stock_price)

        calls_filtered = calls_processed[
            (calls_processed["incremental_percentage"] >= st.session_state.inputs["call_range"][0]) &
            (calls_processed["incremental_percentage"] <= st.session_state.inputs["call_range"][1])
        ]
        puts_filtered = puts_processed[
            (puts_processed["incremental_percentage"] >= st.session_state.inputs["put_range"][0]) &
            (puts_processed["incremental_percentage"] <= st.session_state.inputs["put_range"][1])
        ]

        # Plotting
        fig, axes = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

        def overlay_grid(ax):
            ax.xaxis.set_major_locator(plt.MultipleLocator(1))
            ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.7)

        if st.session_state.inputs["plot_put"]:
            axes[0].plot(puts_filtered["incremental_percentage"], puts_filtered["bid_ratio"], color="blue", label="Bid", marker="o")
            axes[0].plot(puts_filtered["incremental_percentage"], puts_filtered["ask_ratio"], color="orange", label="Ask", marker="o")
            axes[0].set_title(f"{stock_ticker} {next_friday_str} (Put Option Quotes)", fontsize=20)
            axes[0].set_ylabel("Premium / Strike (%)", fontsize=16)
            axes[0].legend(fontsize=14)
            overlay_grid(axes[0])

        if st.session_state.inputs["plot_call"]:
            axes[1].plot(calls_filtered["incremental_percentage"], calls_filtered["bid_ratio"], color="blue", label="Bid", marker="o")
            axes[1].plot(calls_filtered["incremental_percentage"], calls_filtered["ask_ratio"], color="orange", label="Ask", marker="o")
            axes[1].set_title(f"{stock_ticker} {next_friday_str} (Call Option Quotes)", fontsize=20)
            axes[1].set_ylabel("Premium / Strike (%)", fontsize=16)
            axes[1].set_xlabel("(Strike Price - Stock Price) / Stock Price (%)", fontsize=16)
            axes[1].legend(fontsize=14)
            overlay_grid(axes[1])

        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.tight_layout()
        st.pyplot(fig)

except Exception as e:
    st.error(f"An error occurred: {e}")
