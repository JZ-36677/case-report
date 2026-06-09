"""
每日自動抓取股價腳本
由 GitHub Actions 每個交易日收盤後觸發
"""
import yfinance as yf
import json
import os
from datetime import datetime, date, timedelta
import numpy as np

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"last_updated": "", "prices": {"00715L": {}, "2236": {}}, "volatility": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fetch_price(ticker_symbol, date_str=None):
    """抓取股票收盤價"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        # 抓近5天確保能取到最新收盤
        hist = ticker.history(period="5d")
        if hist.empty:
            print(f"⚠ No data for {ticker_symbol}")
            return None, None
        latest = hist.iloc[-1]
        price = round(float(latest["Close"]), 2)
        price_date = hist.index[-1].strftime("%Y-%m-%d")
        print(f"✓ {ticker_symbol}: {price} ({price_date})")
        return price, price_date
    except Exception as e:
        print(f"✗ Error fetching {ticker_symbol}: {e}")
        return None, None

def calc_hist_volatility(ticker_symbol, days=30):
    """計算歷史波動率（年化）作為BIV參考"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="60d")
        if len(hist) < 20:
            return None
        closes = hist["Close"].values
        log_returns = np.log(closes[1:] / closes[:-1])
        # 取最近N天
        recent = log_returns[-min(days, len(log_returns)):]
        vol_daily = recent.std()
        vol_annual = vol_daily * (252 ** 0.5) * 100  # 轉成%
        return round(vol_annual, 2)
    except Exception as e:
        print(f"✗ Error calculating volatility: {e}")
        return None

def main():
    print(f"=== 股價更新 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    data = load_data()

    # 抓 00715L（布蘭特原油正2 ETF）
    price_715, date_715 = fetch_price("0715L.TW")
    if price_715 and date_715:
        data["prices"]["00715L"][date_715] = price_715

    # 抓 2236（百達-KY）
    price_2236, date_2236 = fetch_price("2236.TW")
    if price_2236 and date_2236:
        data["prices"]["2236"][date_2236] = price_2236

    # 計算 00715L 30日歷史波動率
    hv = calc_hist_volatility("0715L.TW", days=30)
    if hv:
        today = date.today().strftime("%Y-%m-%d")
        data["volatility"][today] = hv
        print(f"✓ HV(30d): {hv}%")

    data["last_updated"] = date.today().strftime("%Y-%m-%d")
    save_data(data)
    print(f"=== 更新完成 ===")

if __name__ == "__main__":
    main()
