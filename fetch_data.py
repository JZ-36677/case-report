import json, os, re, copy
from datetime import date, datetime
from math import log, sqrt, exp

DATA_FILE = "data.json"

# ── 備用種子資料 ──
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

# ── B-S 工具 ──
def norm_cdf(x):
    a = [0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429]
    p = 0.3275911
    s = 1 if x >= 0 else -1
    t = 1 / (1 + p * abs(x) / sqrt(2))
    y = 1 - (((((a[4]*t + a[3])*t + a[2])*t + a[1])*t + a[0])*t) * exp(-(x**2)/2) / sqrt(2*3.14159265358979)
    return (1 + s * (2*y - 1)) / 2

def bs_price(S, K, T, r, sig, n):
    if sig <= 0 or T <= 0:
        return 0.0
    d1 = (log(S/K) + (r + sig**2/2)*T) / (sig*sqrt(T))
    d2 = d1 - sig*sqrt(T)
    call = S*norm_cdf(d1) - K*exp(-r*T)*norm_cdf(d2)
    return call * n

def calc_biv(S, K, T, r, n, market_price, tol=1e-6):
    """二分法從市場價格反推 BIV"""
    if S <= 0 or K <= 0 or T <= 0 or market_price <= 0:
        return None
    intrinsic = max(S - K, 0) * n
    if market_price <= intrinsic:
        return None

    low, high = 0.001, 30.0  # 0.1% ~ 3000%
    for _ in range(200):
        mid = (low + high) / 2
        p = bs_price(S, K, T, r, mid, n)
        diff = p - market_price
        if abs(diff) < tol:
            break
        if diff < 0:
            low = mid
        else:
            high = mid
    return round(mid * 100, 2)

def date_diff_years(date_str, expiry="2026-10-12"):
    d1 = datetime.strptime(date_str, "%Y-%m-%d")
    d2 = datetime.strptime(expiry, "%Y-%m-%d")
    return (d2 - d1).days / 365

# ── 資料讀寫 ──
def load_data():
    if not os.path.exists(DATA_FILE):
        print("  ℹ data.json 不存在，使用種子資料")
        return copy.deepcopy(SEED)
    try:
        raw = open(DATA_FILE, 'rb').read()
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        content = raw.decode('utf-8', errors='ignore').replace('\r\n','\n').replace('\r','\n')
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            fixed = re.sub(r',(\s*[}\]])', r'\1', content)
            try:
                data = json.loads(fixed)
                print("  ✓ JSON 自動修復成功")
                return data
            except:
                pass
        print("  ⚠ JSON 無法修復，使用種子資料（歷史資料已還原）")
        return copy.deepcopy(SEED)
    except Exception as e:
        print(f"  ⚠ 讀取失敗：{e}，使用種子資料")
        return copy.deepcopy(SEED)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("  ✓ data.json 已儲存")

# ── 股價抓取 ──
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

# ── 自動計算 BIV ──
def auto_calc_biv(data):
    """對每個有 059427 市場價和 00715L 股價的日期自動算 BIV"""
    K, r, n = 66, 0.0175, 0.07
    prices_715 = data["prices"].get("00715L", {})
    prices_wt  = data["prices"].get("059427", {})

    if "volatility" not in data:
        data["volatility"] = {}

    updated = 0
    for d in sorted(prices_wt.keys()):
        if d not in prices_715:
            continue
        S  = prices_715[d]
        mp = prices_wt[d]
        T  = date_diff_years(d)

        if T <= 0 or mp <= 0:
            continue

        biv = calc_biv(S, K, T, r, n, mp)
        if biv and biv > 0:
            old = data["volatility"].get(d)
            data["volatility"][d] = biv
            if old != biv:
                print(f"  BIV {d}：{biv:.2f}% （S={S}, 市場價={mp}）")
                updated += 1

    if updated:
        print(f"  ✓ 共更新 {updated} 筆 BIV")
    else:
        print("  → 所有日期 BIV 已是最新")

def main():
    today = date.today().strftime("%Y-%m-%d")
    print(f"=== 股價更新 {today} ===\n")
    data = load_data()
    for t in ["00715L","2236","059427"]:
        data["prices"].setdefault(t, {})
    data.setdefault("volatility", {})
    updated = False

    # 抓股票
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

    # 自動算 BIV（從 059427 市場價反推）
    print("[BIV 自動計算]")
    auto_calc_biv(data)
    updated = True
    print()

    data["last_updated"] = today
    save_data(data)
    print(f"\n✅ 完成")

if __name__ == "__main__":
    main()
