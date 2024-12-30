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

# Initialize session state with default values if not already set
if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULT_SETTINGS.copy()

# Load defaults on button click
if st.button("Load Defaults"):
    st.session_state.inputs = DEFAULT_SETTINGS.copy()

# Input fields
st.markdown("<h1 style='text-align: center; font-size: 48px;'>Options Quote Visualizer</h1>", unsafe_allow_html=True)

stock_ticker = st.text_input("Enter stock ticker:", st.session_state.inputs["stock_ticker"])
input_date_str = st.date_input("Enter date:", pd.to_datetime(st.session_state.inputs["input_date_str"])).strftime("%Y-%m-%d")
put_range = st.slider("Put Range (as % of stock price):", -50, 10, st.session_state.inputs["put_range"])
call_range = st.slider("Call Range (as % of stock price):", -10, 50, st.session_state.inputs["call_range"])
plot_put = st.checkbox("Plot Puts", value=st.session_state.inputs["plot_put"])
plot_call = st.checkbox("Plot Calls", value=st.session_state.inputs["plot_call"])

# Update session state inputs with current values
st.session_state.inputs = {
    "stock_ticker": stock_ticker,
    "input_date_str": input_date_str,
    "put_range": put_range,
    "call_range": call_range,
    "plot_put": plot_put,
    "plot_call": plot_call
}

# Find the closest Friday after the input date
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

        # Function to process data for plotting
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
        fig, axes = plt.subplots(2, 1, figsize=(14, 12))

        def overlay_strike_prices(ax, option_data):
            ax2 = ax.twiny()
            ax2.set_xlim(ax.get_xlim())
            strike_labels = option_data["strike"].values
            strike_positions = option_data["incremental_percentage"].values
            ax2.set_xticks(strike_positions)
            ax2.set_xticklabels([f"{strike:.1f}" for strike in strike_labels], rotation=45, ha='right', fontsize=18)
            ax2.set_xlabel("Strike Price", fontsize=24)

        # Plot puts
        if plot_put:
            axes[0].scatter(puts_processed["incremental_percentage"], puts_processed["bid_ratio"], color="blue", label="Bid")
            axes[0].scatter(puts_processed["incremental_percentage"], puts_processed["ask_ratio"], color="orange", label="Ask")
            axes[0].plot(puts_processed["incremental_percentage"], puts_processed["bid_ratio"], color="blue", alpha=0.5)
            axes[0].plot(puts_processed["incremental_percentage"], puts_processed["ask_ratio"], color="orange", alpha=0.5)
            axes[0].set_title(f"{stock_ticker} {next_friday_str} (Put Option Quote)", fontsize=28)
            axes[0].set_xlabel("(Strike Price - Stock Price) / Stock Price (%)", fontsize=26)
            axes[0].set_ylabel("Premium / Strike Price (%)", fontsize=26)
            axes[0].tick_params(axis="both", which="major", labelsize=20)
            axes[0].grid(True, which='both', axis='x', linestyle='--', alpha=0.5)
            overlay_strike_prices(axes[0], puts_processed)
        else:
            axes[0].axis("off")

        # Plot calls
        if plot_call:
            axes[1].scatter(calls_processed["incremental_percentage"], calls_processed["bid_ratio"], color="blue", label="Bid")
            axes[1].scatter(calls_processed["incremental_percentage"], calls_processed["ask_ratio"], color="orange", label="Ask")
            axes[1].plot(calls_processed["incremental_percentage"], calls_processed["bid_ratio"], color="blue", alpha=0.5)
            axes[1].plot(calls_processed["incremental_percentage"], calls_processed["ask_ratio"], color="orange", alpha=0.5)
            axes[1].set_title(f"{stock_ticker} {next_friday_str} (Call Option Quote)", fontsize=28)
            axes[1].set_xlabel("(Strike Price - Stock Price) / Stock Price (%)", fontsize=26)
            axes[1].set_ylabel("Premium / Strike Price (%)", fontsize=26)
            axes[1].tick_params(axis="both", which="major", labelsize=20)
            axes[1].grid(True, which='both', axis='x', linestyle='--', alpha=0.5)
            overlay_strike_prices(axes[1], calls_processed)
        else:
            axes[1].axis("off")

        plt.tight_layout(pad=5.0)
        st.pyplot(fig)

except Exception as e:
    st.error(f"An error occurred: {e}")
