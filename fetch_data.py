"""
每日自動抓取股價腳本 - 使用 TWSE API
由 GitHub Actions 每個交易日收盤後觸發
"""
import json, os, urllib.request, numpy as np
from datetime import date

DATA_FILE = "data.json"

STOCKS = {
    "00715L": "tse_00715L.tw",
    "2236":   "tse_2236.tw",
    "059427": "tse_059427.tw"
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
        tickers=list(data["prices"].keys())
        for ti,ticker in enumerate(tickers):
            f.write(f'    "{ticker}": {{\n')
            dates=sorted(data["prices"][ticker].keys())
            for di,d in enumerate(dates):
                val=data["prices"][ticker][d]
                comma="," if di<len(dates)-1 else ""
                f.write(f'      "{d}": {val:.2f}{comma}\n')
            f.write("    }")
            f.write(",\n" if ti<len(tickers)-1 else "\n")
        f.write("  },\n")
        f.write('  "volatility": {\n')
        vdates=sorted(data["volatility"].keys())
        for vi,vd in enumerate(vdates):
            val=data["volatility"][vd]
            comma="," if vi<len(vdates)-1 else ""
            f.write(f'    "{vd}": {val:.2f}{comma}\n')
        f.write("  }\n")
        f.write("}\n")

def fetch_twse(twse_symbol, name):
    try:
        url=f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={twse_symbol}&json=1&delay=0"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=10) as r:
            raw=json.loads(r.read().decode("utf-8"))
        item=raw.get("msgArray",[])
        if not item:
            print(f"  ⚠ 無資料：{name}"); return None,None
        item=item[0]
        price_str=item.get("z","-")
        date_str=item.get("d","")
        if price_str in("-","0","") or not date_str:
            print(f"  ⚠ 今日尚無收盤：{name}"); return None,None
        price=round(float(price_str),2)
        trade_date=f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        print(f"  ✓ {name}：{price:.2f} 元（{trade_date}）")
        return price,trade_date
    except Exception as e:
        print(f"  ✗ 失敗 {name}：{e}"); return None,None

def calc_hv(ticker_symbol,days=30):
    try:
        import yfinance as yf
        hist=yf.Ticker(ticker_symbol).history(period="60d")
        if len(hist)<10: return None
        closes=hist["Close"].values
        lr=np.log(closes[1:]/closes[:-1])
        return round(lr[-min(days,len(lr)):].std()*(252**.5)*100,2)
    except: return None

def main():
    today=date.today().strftime("%Y-%m-%d")
    print(f"=== 股價更新 {today} ===\n")
    data=load_data()

    # 確保 059427 欄位存在
    if "059427" not in data["prices"]:
        data["prices"]["059427"]={}

    updated=False
    for name,sym in STOCKS.items():
        print(f"[{name}]")
        price,pdate=fetch_twse(sym,name)
        if price and pdate:
            if pdate not in data["prices"][name]:
                data["prices"][name][pdate]=price
                print(f"  → 新增 {pdate}"); updated=True
            else:
                print(f"  → {pdate} 已存在，跳過")
        print()

    print("[波動率]")
    hv=calc_hv("0715L.TW",30)
    if hv:
        data["volatility"][today]=hv
        print(f"  ✓ HV：{hv:.2f}%"); updated=True

    data["last_updated"]=today
    save_data(data)
    print(f"\n{'✅ 更新完成' if updated else '⚠ 無新資料'}")

if __name__=="__main__":
    main()
