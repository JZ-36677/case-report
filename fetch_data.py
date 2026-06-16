"""
每日自動抓取股價 - 使用 TWSE 歷史資料 API（可跨國存取）
GitHub Actions 每個交易日收盤後觸發
"""
import json, os, urllib.request, numpy as np
from datetime import date, datetime

DATA_FILE = "data.json"

STOCKS = {
    "00715L": "00715L",
    "2236":   "2236",
    "059427": "059427"
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated":"","prices":{"00715L":{},"2236":{},"059427":{}},"volatility":{}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write('{\n')
        f.write(f'  "last_updated": "{data["last_updated"]}",\n')
        f.write('  "note": "Auto-updated daily via GitHub Actions.",\n')
        f.write('  "prices": {\n')
        tickers = list(data["prices"].keys())
        for ti, ticker in enumerate(tickers):
            f.write(f'    "{ticker}": {{\n')
            dates = sorted(data["prices"][ticker].keys())
            for di, d in enumerate(dates):
                val = data["prices"][ticker][d]
                comma = "," if di < len(dates)-1 else ""
                f.write(f'      "{d}": {val:.2f}{comma}\n')
            f.write("    }")
            f.write(",\n" if ti < len(tickers)-1 else "\n")
        f.write("  },\n")
        f.write('  "volatility": {\n')
        vdates = sorted(data["volatility"].keys())
        for vi, vd in enumerate(vdates):
            val = data["volatility"][vd]
            comma = "," if vi < len(vdates)-1 else ""
            f.write(f'    "{vd}": {val:.2f}{comma}\n')
        f.write("  }\n")
        f.write("}\n")

def fetch_twse_history(stock_no):
    """
    用 TWSE 公開歷史資料 API 抓當月收盤價
    API: https://www.twse.com.tw/exchangeReport/STOCK_DAY
    回傳最新一個交易日的收盤價與日期
    """
    today = date.today()
    date_param = today.strftime("%Y%m%d")

    url = (f"https://www.twse.com.tw/exchangeReport/STOCK_DAY"
           f"?response=json&date={date_param}&stockNo={stock_no}")

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; stock-data-fetcher)",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = json.loads(r.read().decode("utf-8"))

        if raw.get("stat") != "OK":
            print(f"  ⚠ TWSE 回傳非OK：{raw.get('stat')}")
            return None, None

        data_rows = raw.get("data", [])
        if not data_rows:
            print(f"  ⚠ 無資料行")
            return None, None

        # 取最後一行（最新交易日）
        last = data_rows[-1]
        # 格式：[民國日期, 成交股數, 成交金額, 開盤, 最高, 最低, 收盤, 漲跌, 成交筆數]
        tw_date = last[0].strip()   # 例：115/06/16
        close_str = last[6].strip() # 收盤價

        # 民國轉西元
        parts = tw_date.split("/")
        year = int(parts[0]) + 1911
        month = int(parts[1])
        day = int(parts[2])
        trade_date = f"{year:04d}-{month:02d}-{day:02d}"

        close = round(float(close_str.replace(",", "")), 2)
        print(f"  ✓ {stock_no}：{close:.2f} 元（{trade_date}）")
        return close, trade_date

    except Exception as e:
        print(f"  ✗ 失敗 {stock_no}：{e}")
        return None, None

def calc_hv(days=30):
    """用 yfinance 算 00715L 歷史波動率（備用）"""
    try:
        import yfinance as yf
        hist = yf.Ticker("0715L.TW").history(period="60d")
        if len(hist) < 10:
            return None
        closes = hist["Close"].values
        lr = np.log(closes[1:] / closes[:-1])
        return round(lr[-min(days, len(lr)):].std() * (252 ** 0.5) * 100, 2)
    except:
        return None

def main():
    today = date.today().strftime("%Y-%m-%d")
    print(f"=== 股價更新 {today} ===\n")

    data = load_data()

    # 確保所有欄位存在
    for ticker in STOCKS:
        if ticker not in data["prices"]:
            data["prices"][ticker] = {}

    updated = False

    for name in STOCKS:
        print(f"[{name}]")
        price, pdate = fetch_twse_history(name)
        if price and pdate:
            if pdate not in data["prices"][name]:
                data["prices"][name][pdate] = price
                print(f"  → 新增 {pdate}")
                updated = True
            else:
                print(f"  → {pdate} 已存在，跳過")
        print()

    print("[波動率]")
    hv = calc_hv(30)
    if hv:
        data["volatility"][today] = hv
        print(f"  ✓ HV(30日)：{hv:.2f}%")
        updated = True
    else:
        print("  ⚠ 略過")

    data["last_updated"] = today
    save_data(data)
    print(f"\n{'✅ 更新完成' if updated else '⚠ 無新資料'}")

if __name__ == "__main__":
    main()
