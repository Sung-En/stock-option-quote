import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import streamlit as st

# Streamlit app title
st.title("Options Quote Visualizer")

# Inputs for the app
stock_ticker = st.text_input("Enter stock ticker:", "AAPL")
input_date_str = st.date_input("Enter date:", dt.datetime.now()).strftime("%Y-%m-%d")
put_range = st.slider("Put Range (as % of stock price):", -50, 10, (-20, 5))
call_range = st.slider("Call Range (as % of stock price):", -10, 50, (-5, 20))
plot_put = st.checkbox("Plot Puts", value=True)  # Default to True
plot_call = st.checkbox("Plot Calls", value=False)  # Default to False

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
        fig, axes = plt.subplots(1, 1, figsize=(14, 8))  # Increased figsize for better visibility

        def overlay_strike_prices(ax, option_data):
            ax2 = ax.twiny()
            ax2.set_xlim(ax.get_xlim())
            strike_labels = option_data["strike"].values
            strike_positions = option_data["incremental_percentage"].values
            ax2.set_xticks(strike_positions)
            ax2.set_xticklabels([f"{strike:.1f}" for strike in strike_labels], rotation=45, ha='right')
            ax2.set_xlabel("Strike Price")

        # Plot puts (only if plot_put is True)
        if plot_put:
            # Plot the scatter points
            axes.scatter(puts_processed["incremental_percentage"], puts_processed["bid_ratio"], color="blue", label="Bid")
            axes.scatter(puts_processed["incremental_percentage"], puts_processed["ask_ratio"], color="orange", label="Ask")

            # Plot a line connecting the dots (optional)
            axes.plot(puts_processed["incremental_percentage"], puts_processed["bid_ratio"], color="blue", alpha=0.5)  # Line for bids
            axes.plot(puts_processed["incremental_percentage"], puts_processed["ask_ratio"], color="orange", alpha=0.5)  # Line for asks

            axes.set_title(f"Put Options ({next_friday_str})", fontsize=18)
            axes.set_xlabel("(Strike Price - Stock Price) / Stock Price (%)", fontsize=14)
            axes.set_ylabel("Premium / Strike Price (%)", fontsize=14)
            axes.legend(fontsize=12)
            axes.grid(True)
            overlay_strike_prices(axes, puts_processed)
        else:
            axes.axis("off")  # Hide the axis if plot_put is False

        # Plot calls (only if plot_call is True)
        if plot_call:
            # Plot the scatter points for calls
            axes.scatter(calls_processed["incremental_percentage"], calls_processed["bid_ratio"], color="blue", label="Bid")
            axes.scatter(calls_processed["incremental_percentage"], calls_processed["ask_ratio"], color="orange", label="Ask")

            # Plot a line connecting the dots for calls
            axes.plot(calls_processed["incremental_percentage"], calls_processed["bid_ratio"], color="blue", alpha=0.5)  # Line for bids
            axes.plot(calls_processed["incremental_percentage"], calls_processed["ask_ratio"], color="orange", alpha=0.5)  # Line for asks

            axes.set_title(f"Call Options ({next_friday_str})", fontsize=18)
            axes.set_xlabel("(Strike Price - Stock Price) / Stock Price (%)", fontsize=14)
            axes.set_ylabel("Premium / Strike Price (%)", fontsize=14)
            axes.legend(fontsize=12)
            axes.grid(True)
            overlay_strike_prices(axes, calls_processed)
        else:
            axes.axis("off")  # Hide the axis if plot_call is False

        # Adjust layout and display plot
        plt.tight_layout(pad=5.0)  # Increase padding to make the plot more spacious
        st.pyplot(fig)

except Exception as e:
    st.error(f"An error occurred: {e}")
