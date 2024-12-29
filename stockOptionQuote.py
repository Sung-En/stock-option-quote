import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import streamlit as st

# Manually control whether the script is for Streamlit or PyCharm (set it to True for Streamlit, False for PyCharm)
is_streamlit_control = True  # Set this to True if running in Streamlit

# Streamlit app title
if is_streamlit_control:
    st.title("Options Quote Visualizer")
else:
    print("Running in PyCharm (Console Mode)")

# Control input to switch between Streamlit and PyCharm modes
if is_streamlit_control:
    stock_ticker = st.text_input("Enter stock ticker:", "AAPL")
    input_date_str = st.date_input("Enter date:", dt.datetime.now()).strftime("%Y-%m-%d")
    put_range = st.slider("Put Range (as % of stock price):", -50, 10, (-20, 5))
    call_range = st.slider("Call Range (as % of stock price):", -10, 50, (-5, 20))
    plot_put = st.checkbox("Plot Puts", value=True)
    plot_call = st.checkbox("Plot Calls", value=True)
else:
    # Default values for PyCharm or local environment
    stock_ticker = "AAPL"  # Default stock ticker
    input_date_str = "2025-01-03"  # Default date
    put_range = [-20, 5]  # Default put range (min, max)
    call_range = [-5, 20]  # Default call range (min, max)
    plot_put = True  # Default: plot puts
    plot_call = True  # Default: plot calls
    print(f"Using default values for PyCharm: Stock = {stock_ticker}, Date = {input_date_str}, Put Range = {put_range}, Call Range = {call_range}")

# Parse the date and find the closest Friday
input_date = dt.datetime.strptime(input_date_str, "%Y-%m-%d")
next_friday = input_date + dt.timedelta((4 - input_date.weekday()) % 7)
next_friday_str = next_friday.strftime('%Y-%m-%d')

try:
    # Fetch stock data
    stock = yf.Ticker(stock_ticker)
    expiration_dates = stock.options
    if next_friday_str not in expiration_dates:
        if is_streamlit_control:
            st.error(f"No options data available for {next_friday_str}. Try another date.")
        else:
            print(f"No options data available for {next_friday_str}. Try another date.")
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
        fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

        def overlay_strike_prices(ax, option_data):
            ax2 = ax.twiny()
            ax2.set_xlim(ax.get_xlim())
            strike_labels = option_data["strike"].values
            strike_positions = option_data["incremental_percentage"].values
            ax2.set_xticks(strike_positions)
            ax2.set_xticklabels([f"{strike:.1f}" for strike in strike_labels], rotation=45, ha='right')
            ax2.set_xlabel("Strike Price")

        # Plot calls
        if plot_call:
            axes[1].scatter(calls_processed["incremental_percentage"], calls_processed["bid_ratio"], color="blue", label="Bid")
            axes[1].scatter(calls_processed["incremental_percentage"], calls_processed["ask_ratio"], color="orange", label="Ask")
            axes[1].set_title(f"Call Options ({next_friday_str})")
            axes[1].set_xlabel("(Strike Price - Stock Price) / Stock Price (%)")
            axes[1].legend()
            axes[1].grid(True)
            overlay_strike_prices(axes[1], calls_processed)
        else:
            axes[1].axis("off")

        # Plot puts
        if plot_put:
            axes[0].scatter(puts_processed["incremental_percentage"], puts_processed["bid_ratio"], color="blue", label="Bid")
            axes[0].scatter(puts_processed["incremental_percentage"], puts_processed["ask_ratio"], color="orange", label="Ask")
            axes[0].set_title(f"Put Options ({next_friday_str})")
            axes[0].set_xlabel("(Strike Price - Stock Price) / Stock Price (%)")
            axes[0].set_ylabel("Premium / Strike Price (%)")
            axes[0].legend()
            axes[0].grid(True)
            overlay_strike_prices(axes[0], puts_processed)
        else:
            axes[0].axis("off")

        # Adjust layout and display plot
        plt.tight_layout()

        if is_streamlit_control:
            st.pyplot(fig)  # Display the plot in Streamlit
        else:
            plt.show()  # Display the plot in PyCharm/console

except Exception as e:
    if is_streamlit_control:
        st.error(f"An error occurred: {e}")
    else:
        print(f"An error occurred: {e}")
