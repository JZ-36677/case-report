# 承銷風險評估報告 × B-S 權證定價

> 以承銷商與量化分析師雙重視角，針對兩個實務案例進行系統性評估。
> 支援即時切換評價基準日，每日自動更新股價資料。

🔗 **線上預覽：** [jz-36677.github.io/case-report](https://jz-36677.github.io/case-report/)

-----

## 專案簡介

本報告為金融專業面試準備專案，涵蓋：

|案例 |主題                          |核心工具                 |
|---|----------------------------|---------------------|
|案例一|百達-KY (2236) 無擔保可轉換公司債承銷風險評估|信用分析 × 財報解讀          |
|案例二|059427 SGBR2X國泰5A購01 理論定價   |Black-Scholes 選擇權定價模型|

-----

## 功能特色

### 📊 案例一：CB承銷風險評估

- 財務健康度視覺化（獲利能力、償債能力、成長動能）
- 三大風險相互強化鏈（風險疊加邏輯）
- **承銷商法律責任風險**分析
- 即時切換評價基準日 → 自動更新股價與轉換誘因

### 📐 案例二：B-S 理論定價

- 六個參數全部可手動輸入，無鎖定限制
- **自動預填**：S（標的現貨價）、T（剩餘天數）、σ（波動率）
- 逐步顯示 d₁、d₂、N(d₁)、N(d₂) 完整運算過程
- 敏感度分析圖表（S、σ、T 三維度）
- 模型限制說明（波動率微笑、Heston 模型建議）

### 🔄 自動資料更新

- GitHub Actions 每個交易日 **台灣時間 15:30** 自動抓取收盤價
- 股票代號：`0715L.TW`（00715L）、`2236.TW`（百達-KY）
- 波動率：30 日歷史波動率（年化）作為 BIV 參考值
- 資料存於 `data.json`，網頁直接讀取，無需後端

-----

## 技術架構

```
repo/
├── index.html          # 主網頁（三頁籤式報告）
├── data.json           # 每日自動更新的股價資料
├── fetch_data.py       # Python 股價抓取腳本
└── .github/
    └── workflows/
        └── update_data.yml  # GitHub Actions 排程設定
```

### 前端技術

- **純靜態 HTML**，無框架，直接部署 GitHub Pages
- [Chart.js](https://www.chartjs.org/) — 敏感度分析圖表
- Google Fonts：`Noto Sans TC`（中文）× `IBM Plex Mono`（數字）× `Playfair Display`（標題）

### 資料自動化

- **Python** + `yfinance` 抓取 Yahoo Finance 收盤價
- **GitHub Actions** cron job（UTC 07:30 = 台灣 15:30）
- 每次更新自動 commit：`📈 Auto update stock data YYYY-MM-DD`

-----

## 本地使用

```bash
# 克隆專案
git clone https://github.com/jz-36677/case-report.git
cd case-report

# 直接用瀏覽器打開（需要 data.json 在同目錄）
open index.html

# 手動觸發股價更新
pip install yfinance pandas numpy
python fetch_data.py
```

> ⚠️ 直接打開本地檔案時，`fetch('./data.json')` 會被瀏覽器 CORS 政策擋住。
> 建議用 `python -m http.server 8080` 啟動本地伺服器後再開啟。

-----

## GitHub Actions 設定

首次部署需開啟 Actions 寫入權限：

```
GitHub Repo → Settings
→ Actions → General
→ Workflow permissions
→ ✅ Read and write permissions
→ Save
```

設定完成後，每個交易日收盤後自動執行，也可在 Actions 頁面手動觸發。

-----

## 評價參數說明（案例二基準日：2026/06/08）

|參數|數值     |說明                    |
|--|-------|----------------------|
|S |57.10 元|00715L 收盤價（由 6/9 報價回推）|
|K |66.00 元|履約價（發行條件書載明）          |
|T |126 天  |至到期日 2026/10/12       |
|σ |275.7% |BIV（買方隱含波動率，來源：CMoney）|
|r |1.75%  |台灣1年期公債殖利率            |
|n |0.07   |行使比例（發行條件書載明）         |

**計算結果：**

- 理論價格：**2.21 元**（市場揭示：2.00 元）
- Delta：**0.0536**（市場揭示：0.0527）

-----

## 案例一風險結論

百達-KY (2236) CB 承銷案屬**中高風險**，建議**附條件承接**：

1. 轉換溢價率 110% 遠超市場常態（10–30%），轉換誘因極低
1. 本業 2024 年 EPS -1.01 元，BIGL 併購後負債比從 32% 升至 75%
1. 無擔保條款下，若違約，承銷商面臨投資人法律追訴

**改善條件：** 溢價率調降至 30–50% ＋ 財務維持條款 ＋ 回售條款（Put Option）

-----

## 資料來源

- 股價資料：Yahoo Finance（`yfinance`）
- 隱含波動率（BIV）：[CMoney](https://www.cmoney.tw/)
- 百達-KY 財報：[公開資訊觀測站](https://mops.twse.com.tw/)
- 發行條件：台灣證券交易所

-----

*評價基準日：2026/06/08 ｜ 到期日：2026/10/12 ｜ 本報告僅供學術與求職參考*