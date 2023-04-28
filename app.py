import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title='股票回測應用', layout='wide')  # 移動到 if __name__ == "__main__": 條件之外

st.title('股票回測應用')

# 設定參數
stock_codes = st.text_input("輸入股票代碼，用逗號分隔：")
stock_list = [code.strip() + '.TW' for code in stock_codes.split(',')] if stock_codes else [] # 自動添加 ".TW"
start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')
investment_type = st.selectbox('選擇投資類型', ['lump_sum', 'dollar_cost_averaging'])
initial_investment = st.number_input('初始投資金額', min_value=0, value=100000, step=1000)
dca_frequency = st.selectbox('定期投資頻率', ['monthly', 'quarterly'])
benchmark = '0050.TW'

# ... 省略函數的定義（download_stock_data, calculate_return）
# 請將您原本代碼中的 download_stock_data, calculate_return 函數複製到這裡
def download_stock_data(stock_list, start_date, end_date):
    stock_data = {}
    for stock in stock_list:
        stock_data[stock] = yf.download(stock, start=start_date, end=end_date, auto_adjust=False)
        stock_data[stock]['Dividends'] = yf.Ticker(stock).dividends
        stock_data[stock]['Dividends'].fillna(0, inplace=True)
    return stock_data


def calculate_return(stock_data, investment_type, initial_investment, dca_frequency):
    if investment_type == 'lump_sum':
        portfolio_value = initial_investment / len(stock_data)
        for stock in stock_data:
            stock_data[stock]['return'] = stock_data[stock]['Adj Close'].pct_change()
            stock_data[stock]['cumulative_return'] = (1 + stock_data[stock]['return']).cumprod()
            stock_data[stock]['lump_sum_value'] = stock_data[stock]['cumulative_return'] * portfolio_value

        total_value = sum([stock_data[stock]['lump_sum_value'][-1] for stock in stock_data])
        return total_value

    elif investment_type == 'dollar_cost_averaging':
        total_value = 0
        for stock in stock_data:
            stock_data[stock]['return'] = stock_data[stock]['Adj Close'].pct_change()
            stock_data[stock] = stock_data[stock].resample(dca_frequency).last()
            stock_data[stock]['contribution'] = initial_investment / len(stock_data) / len(stock_data[stock])
            stock_data[stock]['shares_bought'] = stock_data[stock]['contribution'] / stock_data[stock]['Adj Close']
            stock_data[stock]['total_shares'] = stock_data[stock]['shares_bought'].cumsum()
            total_value += stock_data[stock]['total_shares'][-1] * stock_data[stock]['Adj Close'][-1]
        return total_value


def main():
    if stock_codes:
        stock_data = download_stock_data(stock_list + [benchmark], start_date, end_date)
        
        # 股利再投入
        for stock in stock_data:
            stock_data[stock]['Adj Close'] *= (1 + stock_data[stock]['Dividends'] / stock_data[stock]['Close']).cumprod()

        # 計算回測結果
        portfolio_value = calculate_return(stock_data, investment_type, initial_investment, dca_frequency)
        st.write("初始投入金額:", initial_investment)
        st.write("投資組合價值:", portfolio_value)
        
        # 計算指數回測結果
        benchmark_value = calculate_return({benchmark: stock_data[benchmark]}, investment_type, initial_investment, dca_frequency)
        st.write("Benchmark 價值:", benchmark_value)
        
        # 比較回測結果
        performance_difference = portfolio_value - benchmark_value
        st.write("績效差異:", performance_difference)

        # 計算年化報酬率
        years = 5
        portfolio_annualized_return = (portfolio_value / initial_investment) ** (1 / years) - 1
        benchmark_annualized_return = (benchmark_value / initial_investment) ** (1 / years) - 1
        st.write("投資組合年化回報率:", portfolio_annualized_return * 100, "%")
        st.write("Benchmark 年化回報率:", benchmark_annualized_return * 100, "%")

if __name__ == "__main__":
    if st.button('開始回測'):
        main()
