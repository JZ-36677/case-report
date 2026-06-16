"""
每日自動抓取股價腳本
由 GitHub Actions 每個交易日收盤後觸發
"""
import yfinance as yf
import json
import os
from datetime import date, datetime, timedelta
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
    # 用自訂格式輸出，保留小數點後兩位避免 57.10 -> 57.1 的無意義 diff
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write('{\n')
        f.write(f'  "last_updated": "{data["last_updated"]}",\n')
        f.write(f'  "note": "{data.get("note", "Auto-updated daily via GitHub Actions.")}",\n')
        f.write('  "prices": {\n')

        tickers = list(data["prices"].keys())
        for ti, ticker in enumerate(tickers):
            f.write(f'    "{ticker}": {{\n')
            dates = sorted(data["prices"][ticker].keys())
            for di, d in enumerate(dates):
                val = data["prices"][ticker][d]
                comma = "," if di < len(dates) - 1 else ""
                f.write(f'      "{d}": {val:.2f}{comma}\n')
            f.write("    }")
            f.write(",\n" if ti < len(tickers) - 1 else "\n")

        f.write("  },\n")
        f.write('  "volatility": {\n')
        vdates = sorted(data["volatility"].keys())
        for vi, vd in enumerate(vdates):
            val = data["volatility"][vd]
            comma = "," if vi < len(vdates) - 1 else ""
            f.write(f'    "{vd}": {val:.2f}{comma}\n')
        f.write("  }\n")
        f.write("}\n")

def fetch_latest_price(ticker_symbol):
    """抓取最新收盤價，自動重試兩次"""
    for attempt in range(2):
        try:
            ticker = yf.Ticker(ticker_symbol)
            # 抓10天確保有足夠資料
            hist = ticker.history(period="10d")
            if hist.empty:
                print(f"  ⚠ 無資料：{ticker_symbol}（第{attempt+1}次）")
                continue

            # 取最新一筆
            latest_date = hist.index[-1].strftime("%Y-%m-%d")
            latest_price = round(float(hist["Close"].iloc[-1]), 2)
            print(f"  ✓ {ticker_symbol}：{latest_price:.2f} 元（{latest_date}）")
            return latest_price, latest_date

        except Exception as e:
            print(f"  ✗ 第{attempt+1}次失敗 {ticker_symbol}：{e}")

    return None, None

def calc_hist_volatility(ticker_symbol, days=30):
    """計算30日歷史波動率（年化）"""
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
    print(f"=== 每日股價更新 {today} ===\n")

    data = load_data()
    updated = False

    # 00715L
    print("[00715L]")
    price, pdate = fetch_latest_price("0715L.TW")
    if price and pdate:
        if pdate not in data["prices"]["00715L"]:
            data["prices"]["00715L"][pdate] = price
            print(f"  → 新增 {pdate}")
            updated = True
        else:
            print(f"  → {pdate} 已存在，跳過")

    # 2236
    print("\n[2236]")
    price, pdate = fetch_latest_price("2236.TW")
    if price and pdate:
        if pdate not in data["prices"]["2236"]:
            data["prices"]["2236"][pdate] = price
            print(f"  → 新增 {pdate}")
            updated = True
        else:
            print(f"  → {pdate} 已存在，跳過")

    # 波動率
    print("\n[波動率]")
    hv = calc_hist_volatility("0715L.TW", days=30)
    if hv:
        data["volatility"][today] = hv
        print(f"  ✓ HV(30日年化)：{hv:.2f}%")
        updated = True

    # 一定更新日期
    data["last_updated"] = today
    data["note"] = "Auto-updated daily via GitHub Actions."

    save_data(data)

    if updated:
        print(f"\n✅ 有新資料，已寫入 {DATA_FILE}")
    else:
        print(f"\n⚠ 無新資料（可能市場尚未收盤或資料未更新）")

if __name__ == "__main__":
    main()
