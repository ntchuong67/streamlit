import streamlit as st
import plotly.express as px
from tvdatafeed.tvDatafeed.main import *
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt

USERNAME = ''
PASSWORD = ''
tv = TvDatafeed(USERNAME, PASSWORD)

def return_time(time):
    time_intervals = {
        "1h": Interval.in_1_hour,
        "15": Interval.in_15_minute,
        "30": Interval.in_30_minute,
        "1": Interval.in_1_minute,
        "4h": Interval.in_4_hour,
        "2h": Interval.in_2_hour,
        "5": Interval.in_5_minute,
        "3": Interval.in_3_minute,
        "45": Interval.in_45_minute,
        "1d": Interval.in_daily,
        "1w": Interval.in_weekly,
        "1M": Interval.in_monthly
    }
    return time_intervals.get(time, "Unknown time format")


def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

def plot_correlation_matrix(all_data_dict):
    close_prices = pd.DataFrame()
    
    for ticker, data in all_data_dict.items():
        close_prices[ticker] = data['close'].pct_change()
    
    correlation_matrix = close_prices.corr()
    
    fig = px.imshow(correlation_matrix,
                    labels=dict(x="Stock", y="Stock", color="Correlation"),
                    x=correlation_matrix.columns,
                    y=correlation_matrix.columns,
                    color_continuous_scale="RdBu",
                    aspect="auto")
    
    fig.update_traces(text=correlation_matrix.round(2), texttemplate="%{text}")
    fig.update_layout(title_text='Correlation Matrix of Stock Prices')
    st.plotly_chart(fig)
    
    return correlation_matrix, close_prices

def plot_rolling_correlation(close_prices, window_size, factor=None):
    if factor:
        # Tính rolling correlation với factor
        other_tickers = [t for t in close_prices.columns if t != factor]
        all_rolling_corrs = pd.DataFrame(index=close_prices.index)
        
        for ticker in other_tickers:
            rolling_corr = close_prices[ticker].rolling(window=window_size).corr(close_prices[factor])
            all_rolling_corrs[f'{ticker}_vs_{factor}'] = rolling_corr
        
        # Tạo interactive plot với Plotly
        fig = go.Figure()
        
        for column in all_rolling_corrs.columns:
            fig.add_trace(
                go.Scatter(
                    x=all_rolling_corrs.index,
                    y=all_rolling_corrs[column],
                    name=column,
                    mode='lines',
                    hovertemplate='Date: %{x}<br>Correlation: %{y:.4f}<extra></extra>'
                )
            )
        
        fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
        
        fig.update_layout(
            title=f'Rolling Correlation ({window_size} periods) with {factor}',
            xaxis_title='Date',
            yaxis_title='Correlation',
            yaxis_range=[-1, 1],
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.02
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Hiển thị bảng giá trị rolling correlation
        st.subheader("Rolling Correlation Values")
        st.dataframe(all_rolling_corrs.tail(10).style.format("{:.4f}"))
        
        # Download button for all rolling correlations
        csv_rolling = convert_df_to_csv(all_rolling_corrs)
        st.download_button(
            label=f"Download All Rolling Correlations with {factor}",
            data=csv_rolling,
            file_name=f"rolling_correlations_with_{factor}.csv",
            mime='text/csv',
            key='rolling_corr_all'
        )
        
    else:
        # Tính rolling correlation cho tất cả các cặp
        tickers = close_prices.columns
        num_tickers = len(tickers)
        
        for i in range(num_tickers):
            for j in range(i+1, num_tickers):
                ticker1, ticker2 = tickers[i], tickers[j]
                rolling_corr = close_prices[ticker1].rolling(window=window_size).corr(close_prices[ticker2])
                
                # Tạo interactive plot với Plotly
                fig = go.Figure()
                
                fig.add_trace(
                    go.Scatter(
                        x=rolling_corr.index,
                        y=rolling_corr.values,
                        name=f'{ticker1} vs {ticker2}',
                        mode='lines',
                        hovertemplate='Date: %{x}<br>Correlation: %{y:.4f}<extra></extra>'
                    )
                )
                
                fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
                
                fig.update_layout(
                    title=f'Rolling Correlation ({window_size} periods) between {ticker1} and {ticker2}',
                    xaxis_title='Date',
                    yaxis_title='Correlation',
                    yaxis_range=[-1, 1],
                    hovermode='x'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # # DataFrame cho rolling correlation
                # rolling_corr_df = pd.DataFrame({
                #     f'Correlation_{ticker1}_{ticker2}': rolling_corr
                # })
                
                # # Hiển thị bảng giá trị rolling correlation
                # st.subheader(f"Rolling Correlation Values: {ticker1} vs {ticker2}")
                # st.dataframe(rolling_corr_df.style.format("{:.4f}"))
                
                # Download button
                csv_rolling = convert_df_to_csv(rolling_corr_df)
                st.download_button(
                    label=f"Download Rolling Correlation ({ticker1}-{ticker2})",
                    data=csv_rolling,
                    file_name=f"rolling_correlation_{ticker1}_{ticker2}.csv",
                    mime='text/csv',
                    key=f'rolling_corr_{ticker1}_{ticker2}'
                )

st.header("Stock Data")

# Tạo tabs
tab1, tab2 = st.tabs(["Data Download", "Correlation Analysis"])

with tab1:
    # Control for number of inputs
    num_inputs = st.number_input("Number of input rows", min_value=1, max_value=10, value=1)

    # Create input rows
    input_data = []
    for i in range(num_inputs):
        st.subheader(f"Data Input {i+1}")
        
        # Create columns for inputs
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ticker = st.text_input(f'Enter stock tickers', key=f'ticker_{i}').upper()
        with col2:
            exchange = st.text_input(f'Exchange', key=f'exchange_{i}').upper()
        with col3:
            interval = st.text_input(f"Interval", value='1d', key=f'interval_{i}')
        with col4:
            n_bars = st.number_input(f"Number of bars", min_value=1, max_value=20000, 
                                   value=20000, key=f'n_bars_{i}')
        
        input_data.append({
            'ticker': ticker,
            'exchange': exchange,
            'interval': interval,
            'n_bars': n_bars
        })
        
        # Add a separator between input sections
        st.markdown("---")

    if 'all_data_dict' not in st.session_state:
        st.session_state.all_data_dict = {}

    if st.button("Fetch All Data"):
        # Process each input row
        for i, inputs in enumerate(input_data):
            if inputs['ticker'] and inputs['exchange'] and inputs['interval']:
                try:
                    data = tv.get_hist(
                        symbol=inputs['ticker'],
                        exchange=inputs['exchange'],
                        interval=return_time(inputs['interval']),
                        n_bars=inputs['n_bars']
                    )
                    
                    if not data.empty:
                        st.success(f"Data {i+1} ({inputs['ticker']}) retrieved successfully!")
                        st.dataframe(data.tail(10))

                        # Lưu data vào session state
                        st.session_state.all_data_dict[inputs['ticker']] = data

                        # Download button for CSV
                        csv = convert_df_to_csv(data)
                        st.download_button(
                            label=f"Download CSV ({inputs['ticker']})",
                            data=csv,
                            file_name=f"{inputs['ticker']}_{inputs['exchange']}_{inputs['interval']}.csv",
                            mime='text/csv',
                            key=f'csv_{i}'
                        )
                    else:
                        st.warning(f"No data available for {inputs['ticker']}")
                        
                except Exception as e:
                    st.error(f'Error fetching data for {inputs["ticker"]}: {str(e)}')
            else:
                st.warning(f"Please fill in all fields for Data Input {i+1}")

with tab2:
    st.subheader("Correlation Analysis")
    
    # Input cho rolling window size và factor
    col1, col2 = st.columns(2)
    with col1:
        window_size = st.number_input("Rolling Window Size (periods)", min_value=5, max_value=500, value=20)
    with col2:
        if 'all_data_dict' in st.session_state and len(st.session_state.all_data_dict) > 0:
            factor = st.selectbox(
                "Select Factor (optional)", 
                options=['None'] + list(st.session_state.all_data_dict.keys())
            )
        else:
            factor = 'None'
    
    if st.button("Calculate Correlation"):
        if len(st.session_state.all_data_dict) >= 2:
            # Static correlation matrix
            st.subheader("Static Correlation Matrix")
            correlation_matrix, close_prices = plot_correlation_matrix(st.session_state.all_data_dict)
            
            # Download correlation matrix
            csv_corr = convert_df_to_csv(correlation_matrix)
            st.download_button(
                label="Download Correlation Matrix",
                data=csv_corr,
                file_name="correlation_matrix.csv",
                mime='text/csv',
                key='corr_matrix'
            )
            
            # Rolling correlation
            st.subheader(f"Rolling Correlation (Window Size: {window_size} periods)")
            selected_factor = None if factor == 'None' else factor
            plot_rolling_correlation(close_prices, window_size, selected_factor)
            
        else:
            st.info("Please fetch data for at least 2 stocks in the Data Download tab first")