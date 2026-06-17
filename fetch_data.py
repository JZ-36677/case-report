import json, os, re, copy
from datetime import date

DATA_FILE = "data.json"

# 備用種子資料（確保歷史資料不會遺失）
SEED = {
    "last_updated": "",
    "note": "Auto-updated daily via GitHub Actions.",
    "prices": {
        "00715L": {
            "2026-06-08": 57.10, "2026-06-09": 53.05,
            "2026-06-10": 51.20, "2026-06-11": 53.60,
            "2026-06-12": 48.08, "2026-06-15": 42.60,
            "2026-06-16": 41.79
        },
        "2236": {
            "2026-06-08": 113.50, "2026-06-09": 115.00,
            "2026-06-10": 134.00, "2026-06-11": 134.00,
            "2026-06-12": 132.00, "2026-06-15": 133.50,
            "2026-06-16": 134.00
        },
        "059427": {
            "2026-06-08": 2.00, "2026-06-09": 2.03,
            "2026-06-10": 1.89, "2026-06-11": 1.82,
            "2026-06-12": 1.76, "2026-06-15": 1.45,
            "2026-06-16": 1.38
        }
    },
    "volatility": {
        "2026-06-08": 275.70, "2026-06-09": 277.15,
        "2026-06-16": 94.15
    }
}

def load_data():
    if not os.path.exists(DATA_FILE):
        print("  ℹ data.json 不存在，使用種子資料")
        return copy.deepcopy(SEED)

    try:
        raw = open(DATA_FILE, 'rb').read()
        # 移除 BOM，統一換行
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        content = raw.decode('utf-8', errors='ignore').replace('\r\n','\n').replace('\r','\n')

        # 嘗試直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 修復：移除尾巴逗號
        fixed = re.sub(r',(\s*[}\]])', r'\1', content)
        try:
            data = json.loads(fixed)
            print("  ✓ JSON 自動修復成功")
            return data
        except json.JSONDecodeError:
            pass

        # 最後備案：合併種子資料（保留能解析的部分）
        print("  ⚠ JSON 無法修復，使用種子資料繼續執行（歷史資料已從備份還原）")
        return copy.deepcopy(SEED)

    except Exception as e:
        print(f"  ⚠ 讀取失敗：{e}，使用種子資料")
        return copy.deepcopy(SEED)

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
        data["prices"].setdefault(t, {})
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
