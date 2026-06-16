"""
每日自動抓取股價腳本 - 改用 TWSE API（比 yfinance 穩定）
由 GitHub Actions 每個交易日收盤後觸發
"""
import json
import os
import urllib.request
from datetime import date, datetime
import numpy as np

DATA_FILE = "data.json"

# 股票代號對應表（TWSE格式）
STOCKS = {
    "00715L": "tse_00715L.tw",
    "2236":   "tse_2236.tw"
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated": "", "prices": {"00715L": {}, "2236": {}}, "volatility": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write('{\n')
        f.write(f'  "last_updated": "{data["last_updated"]}",\n')
        f.write(f'  "note": "Auto-updated daily via GitHub Actions.",\n')
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

def fetch_twse_price(twse_symbol, ticker_name):
    """用 TWSE 即時行情 API 抓收盤價"""
    try:
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={twse_symbol}&json=1&delay=0"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = json.loads(r.read().decode("utf-8"))

        msgArray = raw.get("msgArray", [])
        if not msgArray:
            print(f"  ⚠ TWSE 無資料：{ticker_name}")
            return None, None

        item = msgArray[0]
        price_str = item.get("z", "-")   # 成交價
        date_str  = item.get("d", "")    # 日期 YYYYMMDD
        if price_str in ("-", "0", "") or not date_str:
            print(f"  ⚠ 今日尚無收盤價：{ticker_name}（可能盤中或未開盤）")
            return None, None

        price = round(float(price_str), 2)
        trade_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        print(f"  ✓ {ticker_name}：{price:.2f} 元（{trade_date}）")
        return price, trade_date

    except Exception as e:
        print(f"  ✗ TWSE 抓取失敗 {ticker_name}：{e}")
        return None, None

def fetch_hist_volatility_yf(ticker_symbol, days=30):
    """用 yfinance 計算歷史波動率（備用）"""
    try:
        import yfinance as yf
        hist = yf.Ticker(ticker_symbol).history(period="60d")
        if len(hist) < 10:
            return None
        closes = hist["Close"].values
        log_returns = np.log(closes[1:] / closes[:-1])
        recent = log_returns[-min(days, len(log_returns)):]
        return round(recent.std() * (252 ** 0.5) * 100, 2)
    except:
        return None

def main():
    today = date.today().strftime("%Y-%m-%d")
    print(f"=== 每日股價更新 {today} ===\n")

    data = load_data()
    updated = False

    for ticker_name, twse_symbol in STOCKS.items():
        print(f"[{ticker_name}]")
        price, pdate = fetch_twse_price(twse_symbol, ticker_name)
        if price and pdate:
            if pdate not in data["prices"][ticker_name]:
                data["prices"][ticker_name][pdate] = price
                print(f"  → 新增 {pdate}")
                updated = True
            else:
                print(f"  → {pdate} 已存在，跳過")
        print()

    # 波動率（yfinance 備用）
    print("[波動率]")
    hv = fetch_hist_volatility_yf("0715L.TW", 30)
    if hv:
        data["volatility"][today] = hv
        print(f"  ✓ HV(30日年化)：{hv:.2f}%")
        updated = True
    else:
        print("  ⚠ 波動率計算略過")

    data["last_updated"] = today
    save_data(data)

    print(f"\n{'✅ 有新資料寫入' if updated else '⚠ 無新資料（請確認市場已收盤）'}")

if __name__ == "__main__":
    main()
