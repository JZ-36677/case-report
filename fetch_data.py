"""
每日自動抓取股價腳本
使用 twstock 套件（專為台灣股市設計，TWSE 官方資料）
"""
import json, os, numpy as np
from datetime import date

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated":"","prices":{"00715L":{},"2236":{},"059427":{}},"volatility":{}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write('{\n')
        f.write(f'  "last_updated": "{data["last_updated"]}",\n')
        f.write('  "note": "Auto-updated daily via GitHub Actions. 059427 manual.",\n')
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

def fetch_twstock(stock_no, name):
    """用 twstock 抓最新收盤價"""
    try:
        import twstock
        stock = twstock.Stock(stock_no)
        if not stock.price or not stock.date:
            print(f"  ⚠ 無資料：{name}")
            return None, None
        price = round(float(stock.price[-1]), 2)
        trade_date = stock.date[-1].strftime("%Y-%m-%d")
        print(f"  ✓ {name}：{price:.2f} 元（{trade_date}）")
        return price, trade_date
    except Exception as e:
        print(f"  ✗ 失敗 {name}：{e}")
        return None, None

def calc_hv(stock_no, days=30):
    """用 twstock 計算歷史波動率"""
    try:
        import twstock
        from math import log
        stock = twstock.Stock(stock_no)
        prices = stock.price
        if len(prices) < 10:
            return None
        closes = prices[-min(60, len(prices)):]
        lr = [log(closes[i]/closes[i-1]) for i in range(1, len(closes))]
        recent = lr[-min(days, len(lr)):]
        avg = sum(recent) / len(recent)
        variance = sum((x-avg)**2 for x in recent) / len(recent)
        hv = (variance ** 0.5) * (252 ** 0.5) * 100
        return round(hv, 2)
    except:
        return None

def main():
    today = date.today().strftime("%Y-%m-%d")
    print(f"=== 股價更新 {today} ===\n")
    data = load_data()
    for t in ["00715L","2236","059427"]:
        if t not in data["prices"]:
            data["prices"][t] = {}
    updated = False

    for name in ["00715L", "2236"]:
        print(f"[{name}]")
        p, d = fetch_twstock(name, name)
        if p and d:
            if d not in data["prices"][name]:
                data["prices"][name][d] = p
                print(f"  → 新增 {d}"); updated = True
            else:
                print(f"  → {d} 已存在，跳過")
        print()

    print("[059427] 權證，需手動更新 data.json\n")

    print("[波動率]")
    hv = calc_hv("00715L", 30)
    if hv:
        data["volatility"][today] = hv
        print(f"  ✓ HV(30日)：{hv:.2f}%")
        updated = True
    else:
        print("  ⚠ 略過")

    data["last_updated"] = today
    save_data(data)
    print(f"\n{'✅ 完成' if updated else '⚠ 無新資料'}")

if __name__ == "__main__":
    main()
