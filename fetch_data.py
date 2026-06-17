import json, os, re, numpy as np
from datetime import date

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"last_updated":"","prices":{"00715L":{},"2236":{},"059427":{}},"volatility":{}}

    with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
        content = f.read().strip()

    # 移除 BOM
    if content.startswith('\ufeff'):
        content = content[1:]

    # 嘗試直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"⚠ JSON 解析失敗：{e}")
        print("⚠ 嘗試自動修復尾巴逗號...")

    # 自動修復：移除 } ] 前的多餘逗號
    fixed = re.sub(r',(\s*[}\]])', r'\1', content)
    try:
        data = json.loads(fixed)
        print("✓ 自動修復成功，繼續執行")
        return data
    except json.JSONDecodeError as e2:
        print(f"✗ 無法自動修復：{e2}")
        print("✗ 腳本中止，保護現有資料")
        raise SystemExit(1)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("  ✓ data.json 已儲存")

def fetch_twstock(stock_no, name):
    try:
        import twstock
        stock = twstock.Stock(stock_no)
        if not stock.price or not stock.date:
            print(f"  ⚠ 無資料：{name}"); return None, None
        price = round(float(stock.price[-1]), 2)
        trade_date = stock.date[-1].strftime("%Y-%m-%d")
        print(f"  ✓ {name}：{price:.2f} 元（{trade_date}）")
        return price, trade_date
    except Exception as e:
        print(f"  ✗ 失敗 {name}：{e}"); return None, None

def calc_hv(stock_no, days=30):
    try:
        import twstock
        from math import log, sqrt
        stock = twstock.Stock(stock_no)
        prices = stock.price
        if len(prices) < 10: return None
        closes = prices[-min(60, len(prices)):]
        lr = [log(closes[i]/closes[i-1]) for i in range(1, len(closes))]
        recent = lr[-min(days, len(lr)):]
        avg = sum(recent)/len(recent)
        variance = sum((x-avg)**2 for x in recent)/len(recent)
        return round((variance**0.5) * (252**0.5) * 100, 2)
    except: return None

def main():
    today = date.today().strftime("%Y-%m-%d")
    print(f"=== 股價更新 {today} ===\n")
    data = load_data()
    for t in ["00715L","2236","059427"]:
        if t not in data.get("prices",{}):
            data.setdefault("prices",{})[t] = {}
    updated = False

    for name in ["00715L","2236"]:
        print(f"[{name}]")
        p, d = fetch_twstock(name, name)
        if p and d:
            if d not in data["prices"][name]:
                data["prices"][name][d] = p
                print(f"  → 新增 {d}"); updated = True
            else:
                print(f"  → {d} 已存在，跳過")
        print()

    print("[059427] 權證需手動更新\n")

    print("[波動率]")
    hv = calc_hv("00715L", 30)
    if hv:
        data["volatility"][today] = hv
        print(f"  ✓ HV：{hv:.2f}%"); updated = True

    data["last_updated"] = today
    save_data(data)
    print(f"\n{'✅ 完成' if updated else '⚠ 無新資料'}")

if __name__ == "__main__":
    main()
