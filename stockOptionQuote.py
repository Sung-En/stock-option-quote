import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import streamlit as st
from streamlit_local_storage import LocalStorage

# Initialize local storage
local_storage = LocalStorage()

# Load previous settings if available
stored_settings = local_storage.get_item("user_settings")
default_settings = {
    "stock_ticker": "AAPL",
    "input_date": dt.datetime.now().strftime("%Y-%m-%d"),
    "put_range": (-20, 5),
    "call_range": (-5, 20),
    "plot_put": True,
    "plot_call": False,
}

# Use stored settings or default
if stored_settings is not None:
    user_settings = stored_settings
else:
    user_settings = default_settings

# Streamlit app title
st.title("Options Quote Visualizer")

# Inputs for the app
stock_ticker = st.text_input("Enter stock ticker:", user_settings["stock_ticker"])
input_date_str = st.date_input("Enter date:", dt.datetime.strptime(user_settings["input_date"], "%Y-%m-%d")).strftime("%Y-%m-%d")
put_range = st.slider("Put Range (as % of stock price):", -50, 10, user_settings["put_range"])
call_range = st.slider("Call Range (as % of stock price):", -10, 50, user_settings["call_range"])
plot_put = st.checkbox("Plot Puts", value=user_settings["plot_put"])
plot_call = st.checkbox("Plot Calls", value=user_settings["plot_call"])

# Save settings on update
def save_settings():
    new_settings = {
        "stock_ticker": stock_ticker,
        "input_date": input_date_str,
        "put_range": put_range,
        "call_range": call_range,
        "plot_put": plot_put,
        "plot_call": plot_call,
    }
    local_storage.set_item("user_settings", new_settings)

st.button("Save Settings", on_click=save_settings)
st.button("Load Default", on_click=lambda: local_storage.set_item("user_settings", default_settings))

# Determine the closest Friday after the input date
input_date = dt.datetime.strptime(input_date_str, "%Y-%m-%d")
next_friday = input_date + dt.timedelta((4 - input_date.weekday()) % 7)
next_friday_str = next_friday.strftime('%Y-%m-%d')

try:
    # Fetch stock data
    stock = yf.Ticker(stock_ticker)
    expiration_dates = stock.options
    if next_friday_str not in expiration_dates:
        st.error(f"No options data available for {next_friday_str}. Try another date.")
    else:
        # Fetch options data for next Friday
        calls = stock.option_chain(next_friday_str).calls
        puts = stock.option_chain(next_friday_str).puts

        # Fetch current stock price
        stock_price = stock.history(period="1d")['Close'].iloc[-1]

        # Process data for plotting
        def process_option_data(option_data, stock_price):
            option_data = option_data.copy()
            option_data["incremental_percentage"] = (option_data["strike"] - stock_price) / stock_price * 100
            option_data["bid_ratio"] = option_data["bid"] / option_data["strike"] * 100
            option_data["ask_ratio"] = option_data["ask"] / option_data["strike"] * 100
            return option_data

        # Process calls and puts data
        calls_processed = process_option_data(calls, stock_price)
        puts_processed = process_option_data(puts, stock_price)

        # Filter data for the specified x-axis range
        calls_processed = calls_processed[
            (calls_processed["incremental_percentage"] >= call_range[0]) &
            (calls_processed["incremental_percentage"] <= call_range[1])
        ]
        puts_processed = puts_processed[
            (puts_processed["incremental_percentage"] >= put_range[0]) &
            (puts_processed["incremental_percentage"] <= put_range[1])
        ]

        # Plotting
        fig, axes = plt.subplots(2, 1, figsize=(10, 12), sharex=True)
        plt.subplots_adjust(hspace=0.5)

        def overlay_strike_prices(ax, option_data):
            ax2 = ax.twiny()
            ax2.set_xlim(ax.get_xlim())
            strike_labels = option_data["strike"].values
            strike_positions = option_data["incremental_percentage"].values
            ax2.set_xticks(strike_positions)
            ax2.set_xticklabels([f"{strike:.1f}" for strike in strike_labels], rotation=45, ha='right')
            ax2.set_xlabel("Strike Price", fontsize=14)

        # Plot puts
        if plot_put:
            axes[0].plot(puts_processed["incremental_percentage"], puts_processed["bid_ratio"], color="blue", label="Bid")
            axes[0].plot(puts_processed["incremental_percentage"], puts_processed["ask_ratio"], color="orange", label="Ask")
            axes[0].set_title(f"{stock_ticker.upper()} {next_friday_str} (Put Option Quotes)", fontsize=18)
            axes[0].set_xlabel("(Strike Price - Stock Price) / Stock Price (%)", fontsize=14)
            axes[0].set_ylabel("Premium / Strike Price (%)", fontsize=14)
            axes[0].grid(True, axis="x", which="both", linestyle="--", linewidth=0.5)
            overlay_strike_prices(axes[0], puts_processed)

        # Plot calls
        if plot_call:
            axes[1].plot(calls_processed["incremental_percentage"], calls_processed["bid_ratio"], color="blue", label="Bid")
            axes[1].plot(calls_processed["incremental_percentage"], calls_processed["ask_ratio"], color="orange", label="Ask")
            axes[1].set_title(f"{stock_ticker.upper()} {next_friday_str} (Call Option Quotes)", fontsize=18)
            axes[1].set_xlabel("(Strike Price - Stock Price) / Stock Price (%)", fontsize=14)
            axes[1].set_ylabel("Premium / Strike Price (%)", fontsize=14)
            axes[1].grid(True, axis="x", which="both", linestyle="--", linewidth=0.5)
            overlay_strike_prices(axes[1], calls_processed)

        st.pyplot(fig)

except Exception as e:
    st.error(f"An error occurred: {e}")