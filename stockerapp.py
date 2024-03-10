import requests
from bs4 import BeautifulSoup
import streamlit as st
import textwrap
import os
import google.generativeai as genai
from IPython.display import Markdown
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import tradingview_ta


# Function to scrape data
@st.cache_data(ttl=600)  # Set the time-to-live (TTL) for 10 minutes
def scrape_moneycontrol_news(pages):
    news_data = []

    for i in range(1, pages + 1):
        url = f'https://www.moneycontrol.com/news/business/stocks/page-{i}'
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            li_elements = soup.find_all('li', class_="clearfix")

            for li_element in li_elements:
                h2_tag = li_element.find('h2')
                a_tag = h2_tag.find('a')
                href_attribute = a_tag.get('href')
                sub_text = li_element.find('p')

                if a_tag:
                    news_data.append({
                        'link': href_attribute,
                        'title': a_tag.text.strip(),
                        'summary': sub_text.text.strip()
                    })

    return news_data


# Set your Google API key here
GOOGLE_API_KEY = 'AIzaSyAcVsSxF30Uh7VFP3p4wexJimVR8x9O_qY'
genai.configure(api_key=GOOGLE_API_KEY)


def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))


# Streamlit App
def main():
    # Initialize session state
    if 'button_clicked' not in st.session_state:
        st.session_state.button_clicked = False

    # Declare news_data outside the button block
    news_data = []
    news_data_dict = []  # Store news data in dictionary form

    # Apply HTML styling to reduce font size
    st.markdown(
        "<h1 style='font-size:32px;text-align:center;'>News Scraper</h1>",
        unsafe_allow_html=True
    )

    pages = st.slider("Select the number of pages to scrape", 1, 20, 1)

    if st.button("Scrape News"):
        news_data = scrape_moneycontrol_news(pages)
        news_data_dict = [{'title': item['title'], 'summary': item['summary']} for item in news_data]
        st.markdown(f"<h2 style='font-size:20px;'>{pages} Pages Successfully Scraped</h2>", unsafe_allow_html=True)

        # Display the URLs of scraped pages as clickable links
        for i in range(1, pages + 1):
            scraped_url = f'https://www.moneycontrol.com/news/business/stocks/page-{i}'
            st.markdown(f"- [Page {i}]({scraped_url})", unsafe_allow_html=True)

        # Display news headlines and subtext
        st.markdown("<h2 style='font-size:20px;'>Scraped News</h2>", unsafe_allow_html=True)
        # toggle_button_clicked = st.button("Toggle News")

        with st.expander("News"):
            for idx, news_item in enumerate(news_data_dict, start=1):
                st.write(f"<span style='font-size: 14px; margin-bottom: 5px;'>{idx}. <strong>{news_item['title']}</strong></span>",
                         unsafe_allow_html=True)
                st.write(f"<span style='font-size: 12px;'>   *{news_item['summary']}*</span>", unsafe_allow_html=True)
                st.write("")

    st.markdown("<h1 style='font-size:32px;text-align:center;'>News Analysis</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-size:25px;'>Ask Anything...</h2>", unsafe_allow_html=True)
    prompt = st.text_input('Example:  stocks with highly positive sentiment/ stocks recommended to buy',
                           placeholder='Write Your Prompt Here...', label_visibility='visible')

    model = genai.GenerativeModel('gemini-pro')

    if st.button(':black[Apply]', use_container_width=True):
        news_data1 = scrape_moneycontrol_news(pages)
        news_data_dict1 = [{'title': item['title'], 'summary': item['summary']} for item in news_data1]
        all_news_data = {}

        # Build a concatenated string of all titles and summaries
        all_news_text = ""
        for idx, news_item in enumerate(news_data_dict1, start=1):
            all_news_data[idx] = {'title': news_item['title'], 'summary': news_item['summary']}
            all_news_text += f"{news_item['title']} {news_item['summary']}. "

        prompt_text = f" {all_news_text} and answer {prompt}"
        response = model.generate_content(prompt_text)

        # Debugging print statements
        print("Prompt Text:", prompt_text)
        print("Response Parts:", response.parts)
        print("Prompt Feedback:", response.prompt_feedback)

        st.write('')
        st.header(":black[Response]")
        st.write('')
        st.markdown(response.text)

    # Text input widget for user input
    st.markdown("<h1 style='font-size:32px;text-align:center;'>Stock Charts</h1>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    # Input for Stock Symbol
    # user_input = st.text_input("Write Stock Symbol Here...").upper()
    with col1:
        # st.write(f"Converted Stock Symbol: {user_input}")
        user_input = st.text_input("Write Stock Symbol Here...").upper().replace(" ", "")
        # user_input = user_input.replace(" ", "")
    with col2:
        symbol_user = st.write(f"Stock Symbol = {user_input}.NS")
        symbol = f'{user_input}.NS'
    # Input for Start Date
    with col3:
        start_date = st.date_input("Select start date", help="Choose a start date")
    # Input for End Date
    with col4:
        end_date = st.date_input("Select end date", help="Choose an end date")
    # symbol = user_input
    df = yf.download(symbol, start=start_date, end=end_date)
    # Add 'Date' column next to the index
    df['Date'] = df.index
    # Reset the index
    df = df.reset_index(drop=True)
    # Add a new column 'Volume Change' with the change in volume
    df['Volume Change'] = df['Volume'].diff()
    # df
    st.markdown("<h2 style='font-size:25px;'>Candlestick Chart</h2>", unsafe_allow_html=True)

    def plot_candlestick_chart(df):
        # Create a candlestick chart using Plotly
        candlestick_fig = go.Figure(
            data=[go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        # Set chart layout for the candlestick chart
        candlestick_fig.update_layout(title=f'Candlestick Chart of {symbol}', xaxis_title='Date',
                                      yaxis_title='Stock Price')

        return candlestick_fig

    st.plotly_chart(plot_candlestick_chart(df))

    def plot_line_chart(df, symbol):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', name='Close Price'))
        fig.update_layout(title=f'Line chart of Close Prices - {symbol}', xaxis_title='Date',
                          yaxis_title='Stock Price')
        return fig

    def plot_volume_chart(df, symbol):
        volume_fig = go.Figure()
        df['Volume Change'] = df['Volume'].diff()
        positive_trace = go.Bar(x=df['Date'][df['Volume Change'] > 0], y=df['Volume'][df['Volume Change'] > 0],
                                name='Positive Volume Change', marker=dict(color='green'))
        negative_trace = go.Bar(x=df['Date'][df['Volume Change'] <= 0], y=df['Volume'][df['Volume Change'] <= 0],
                                name='Negative Volume Change', marker=dict(color='red'))
        volume_fig.update_layout(title=f'Volume for {symbol}', xaxis=dict(title='Date'), yaxis=dict(title='Volume'),
                                 legend=dict(title='Stock Volume'))
        volume_fig.add_traces([positive_trace, negative_trace])
        return volume_fig

    def plot_combined_chart(df, symbol):
        combined_fig = go.Figure()
        line_trace = go.Scatter(x=df['Date'], y=df['Close'], mode='lines', name='Close Price', yaxis='y2')
        positive_trace = go.Bar(x=df['Date'][df['Volume Change'] > 0], y=df['Volume Change'][df['Volume Change'] > 0],
                                name='Positive Volume Change ', marker=dict(color='green'))
        negative_trace = go.Bar(x=df['Date'][df['Volume Change'] <= 0], y=df['Volume Change'][df['Volume Change'] <= 0],
                                name='Negative Volume Change ', marker=dict(color='red'))
        combined_fig.update_layout(title=f'Volume Change Vs Close Price - {symbol}', xaxis=dict(title='Date'),
                                   yaxis=dict(title='Volume Change'), yaxis2=dict(title='Close Price', overlaying='y',
                                                                               side='right'),
                                   legend=dict(title='Volume Change'))
        combined_fig.add_traces([positive_trace, negative_trace, line_trace])
        return combined_fig

    def plot_returns_chart(df, symbol):
        df['Daily Returns'] = df['Close'] - df['Open'].shift(1)

        df.dropna(inplace=True)
        returns_fig = go.Figure()

        returns_trace = go.Bar(x=df['Date'], y=df['Daily Returns'],
                               marker_color=df['Daily Returns'].apply(lambda x: 'green' if x > 0 else 'red'),
                               name='Daily Returns in Rupees')

        returns_fig.update_layout(title=f'Daily Returns in Rupees for {symbol}', xaxis=dict(title='Date'),
                                  yaxis=dict(title='Daily Returns (Rupees)'), legend=dict(title=''))

        returns_fig.add_trace(returns_trace)
        return returns_fig

    st.markdown("<h2 style='font-size:25px;'>Other Charts</h2>", unsafe_allow_html=True)
    
    chart_selection = st.selectbox("Select Chart Type:",
                                   ["Line", "Volume", "Close vs Volume Change", "Daily Returns"])
    
    if chart_selection == "Line":
        st.plotly_chart(plot_line_chart(df, symbol))
    elif chart_selection == "Volume":
        st.plotly_chart(plot_volume_chart(df, symbol))
    elif chart_selection == "Close vs Volume Change":
        st.plotly_chart(plot_combined_chart(df, symbol))
    elif chart_selection == "Daily Returns":
        st.plotly_chart(plot_returns_chart(df, symbol))
    
    st.markdown("<h1 style='font-size:32px;text-align:center;'>Technical Indicators</h1>", unsafe_allow_html=True)

    def get_recommendations(symbol):
        from tradingview_ta import TA_Handler, Interval, Exchange

        # Check if the symbol is not empty
        if not symbol:
            raise ValueError("Symbol is empty. Please enter a valid symbol.")

        handler = TA_Handler(
            symbol=symbol,
            screener="india",
            exchange="NSE",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        return analysis

    default_symbol = user_input
    symbol2 = st.text_input("Enter Stock Symbol (e.g., RELIANCE):", default_symbol)
    if st.button("Get Recommendations"):
        try:
            recommendations = get_recommendations(symbol2).summary
            # st.header("Recommendations:")
            # st.write(recommendations)
            # Iterate through the dictionary and print each key-value pair in bold
            for key, value in recommendations.items():
                # st.write(f"**{key}: {value}**")
                st.markdown(f"<span style='color: black; font-weight: bold;'>{key}: {value}</span>", unsafe_allow_html=True)

            st.markdown("<h2 style='font-size:25px;'>Technical Analysis Indicators</h2>", unsafe_allow_html=True)
            # Create expanders for different categories
            with st.expander("Oscillators"):
                # Iterate through the oscillators and print each key-value pair in bold
                for key, value in get_recommendations(symbol2).oscillators.items():
                    st.markdown(f"<span style='font-weight: bold;'>{key}: {value}</span>", unsafe_allow_html=True)

            with st.expander("Moving Averages"):
                # Iterate through the moving averages and print each key-value pair in bold
                for key, value in get_recommendations(symbol2).moving_averages.items():
                    st.markdown(f"<span style='font-weight: bold;'>{key}: {value}</span>", unsafe_allow_html=True)

            with st.expander("Technical Indicators"):
                # Iterate through the technical indicators and print each key-value pair in bold
                for key, value in get_recommendations(symbol2).indicators.items():
                    st.markdown(f"<span style='font-weight: bold;'>{key}: {value}</span>", unsafe_allow_html=True)

        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    main()
