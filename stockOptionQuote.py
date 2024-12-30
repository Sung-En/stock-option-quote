import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import streamlit as st
from streamlit_localstorage import LocalStorage

# LocalStorage object to handle persistent input settings
local_storage = LocalStorage()

# Default settings
DEFAULT_SETTINGS = {
    "stock_ticker": "AAPL",
    "input_date_str": dt.datetime.now().strftime("%Y-%m-%d"),
    "put_range": (-20, 5),
    "call_range": (-5, 20),
    "plot_put": True,
    "plot_call": False
}

# Fetch settings from local storage or use default
stored_settings = local_storage.get("user_settings")
if stored_settings:
    settings = stored_settings
else:
    settings = DEFAULT_SETTINGS.copy()

# UI Components
st.title("Options Quote Visualizer")
stock_ticker = st.text_input("Enter stock ticker:", settings["stock_ticker"])
input_date_str = st.date_input("Enter date:", pd.to_datetime(settings["input_date_str"]))
put_range = st.slider("Put Range (as % of stock price):", -50, 10, settings["put_range"])
call_range = st.slider("Call Range (as % of stock price):", -10, 50, settings["call_range"])
plot_put = st.checkbox("Plot Puts", value=settings["plot_put"])
plot_call = st.checkbox("Plot Calls", value=settings["plot_call"])

# Update settings
settings.update({
    "stock_ticker": stock_ticker,
    "input_date_str": input_date_str.strftime("%Y-%m-%d"),
    "put_range": put_range,
    "call_range": call_range,
    "plot_put": plot_put,
    "plot_call": plot_call
})

# Save settings to local storage
local_storage.set("user_settings", settings)

# Logic to reset to defaults
if st.button("Load Defaults"):
    settings = DEFAULT_SETTINGS.copy()
    local_storage.set("user_settings", settings)

# Functionality to plot options data
try:
    stock = yf.Ticker(stock_ticker)
    expiration_dates = stock.options
    input_date = dt.datetime.strptime(settings["input_date_str"], "%Y-%m-%d")
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
            (calls_processed["incremental_percentage"] >= settings["call_range"][0]) &
            (calls_processed["incremental_percentage"] <= settings["call_range"][1])
        ]
        puts_filtered = puts_processed[
            (puts_processed["incremental_percentage"] >= settings["put_range"][0]) &
            (puts_processed["incremental_percentage"] <= settings["put_range"][1])
        ]

        # Plotting
        fig, ax = plt.subplots(figsize=(12, 8))

        if plot_put:
            ax.plot(puts_filtered["incremental_percentage"], puts_filtered["bid_ratio"], color="blue", label="Put Bid", marker="o")
            ax.plot(puts_filtered["incremental_percentage"], puts_filtered["ask_ratio"], color="orange", label="Put Ask", marker="o")

        if plot_call:
            ax.plot(calls_filtered["incremental_percentage"], calls_filtered["bid_ratio"], color="green", label="Call Bid", marker="x")
            ax.plot(calls_filtered["incremental_percentage"], calls_filtered["ask_ratio"], color="red", label="Call Ask", marker="x")

        ax.set_xticks(puts_filtered["incremental_percentage"])
        ax.set_xticklabels([f"{s:.1f}\n({int(strike)})" for s, strike in zip(puts_filtered["incremental_percentage"], puts_filtered["strike"])], fontsize=12)

        ax.set_title(f"{stock_ticker} {next_friday_str} (Put Option Quotes)", fontsize=20)
        ax.set_xlabel("(Strike Price - Stock Price) / Stock Price (%)", fontsize=16)
        ax.set_ylabel("Premium / Strike (%)", fontsize=16)
        ax.legend(fontsize=14)
        ax.grid(True, which='both', linestyle='--', linewidth=0.7)

        plt.yticks(fontsize=14)
        plt.tight_layout()
        st.pyplot(fig)

except Exception as e:
    st.error(f"An error occurred: {e}")
