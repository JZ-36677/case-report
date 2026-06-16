"""
每日自動抓取股價腳本
由 GitHub Actions 每個交易日收盤後觸發
"""
import yfinance as yf
import json
import os
from datetime import date
import numpy as np

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "last_updated": "",
        "prices": {"00715L": {}, "2236": {}},
        "volatility": {}
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fetch_price(ticker_symbol):
    """抓取最新收盤價，回傳 (價格, 日期) 或 (None, None)"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="5d")
        if hist.empty:
            print(f"  ⚠ 無資料：{ticker_symbol}")
            return None, None
        price = round(float(hist["Close"].iloc[-1]), 2)
        price_date = hist.index[-1].strftime("%Y-%m-%d")
        print(f"  ✓ {ticker_symbol}：{price} 元（{price_date}）")
        return price, price_date
    except Exception as e:
        print(f"  ✗ 抓取失敗 {ticker_symbol}：{e}")
        return None, None

def calc_hist_volatility(ticker_symbol, days=30):
    """計算30日歷史波動率（年化），作為BIV參考值"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="60d")
        if len(hist) < 10:
            return None
        closes = hist["Close"].values
        log_returns = np.log(closes[1:] / closes[:-1])
        recent = log_returns[-min(days, len(log_returns)):]
        vol_annual = recent.std() * (252 ** 0.5) * 100
        return round(vol_annual, 2)
    except Exception as e:
        print(f"  ✗ 波動率計算失敗：{e}")
        return None

def main():
    today = date.today().strftime("%Y-%m-%d")
    print(f"=== 每日股價更新 {today} ===")

    data = load_data()

    # 00715L（布蘭特原油正2 ETF）
    print("\n[00715L]")
    price, pdate = fetch_price("0715L.TW")
    if price and pdate:
        data["prices"]["00715L"][pdate] = price

    # 2236（百達-KY）
    print("\n[2236]")
    price, pdate = fetch_price("2236.TW")
    if price and pdate:
        data["prices"]["2236"][pdate] = price

    # 00715L 30日歷史波動率
    print("\n[波動率]")
    hv = calc_hist_volatility("0715L.TW", days=30)
    if hv:
        data["volatility"][today] = hv
        print(f"  ✓ HV(30日年化)：{hv}%")
    else:
        print("  ⚠ 波動率計算失敗，跳過")

    data["last_updated"] = today
    data["note"] = "Auto-updated daily via GitHub Actions."

    save_data(data)
    print(f"\n=== 更新完成，已寫入 {DATA_FILE} ===")

if __name__ == "__main__":
    main()
