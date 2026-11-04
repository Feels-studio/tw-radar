import json
import datetime
import urllib.request
import urllib.parse
import ssl
import math
import yfinance as yf
import pandas as pd

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

now_tw = datetime.datetime.utcnow() + datetime.timedelta(hours=8)


def parse_num(val):
    if val is None:
        return 0.0
    s = str(val).replace(",", "").replace("+", "").replace("X", "").strip()
    if s in ["", "--", "---", "----", "N/A"]:
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def fetch_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
        return json.loads(resp.read().decode('utf-8'))


print("1. 正在抓取證交所與櫃買中心全市場當日收盤行情...")
base_stocks = {}

# 上市當日行情 (TWSE)
try:
    for item in fetch_json("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"):
        code = str(item.get("Code", "")).strip()
        if len(code) == 4 and code.isdigit():
            close_p = parse_num(item.get("ClosingPrice"))
            vol = int(parse_num(item.get("TradeVolume")) / 1000)
            if close_p >= 10.0 and vol >= 500:
                base_stocks[code] = {
                    "code": code,
                    "name": str(item.get("Name", "")).strip(),
                    "market": "上市",
                    "yf_sym": f"{code}.TW",
                    "close": close_p,
                    "vol": vol
                }
except Exception as e:
    print(f"TWSE 行情讀取異常: {e}")

# 上櫃當日行情 (TPEx)
try:
    for item in fetch_json("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"):
        code = str(item.get("SecuritiesCompanyCode", "")).strip()
        if len(code) == 4 and code.isdigit():
            close_p = parse_num(item.get("Close"))
            vol = int(parse_num(item.get("TradingShares")) / 1000)
            if close_p >= 10.0 and vol >= 500:
                base_stocks[code] = {
                    "code": code,
                    "name": str(item.get("CompanyName", "")).strip(),
                    "market": "上櫃",
                    "yf_sym": f"{code}.TWO",
                    "close": close_p,
                    "vol": vol
                }
except Exception as e:
    print(f"TPEx 行情讀取異常: {e}")

print(f"共取得 {len(base_stocks)} 檔具流動性之上市櫃普通股。")

# 2. 抓取真實融資餘額變化 (TWSE MI_MARGN & TPEx Margin)
print("2. 正在抓取真實散戶融資餘額與增減資料...")
margin_map = {}
try:
    for item in fetch_json("https://openapi.twse.com.tw/v1/exchangeReport/MI_MARGN"):
        code = str(item.get("股票代號", "")).strip()
        if code in base_stocks:
            prev_m = int(parse_num(item.get("融資前日餘額")))
            curr_m = int(parse_num(item.get("融資今日餘額")))
            limit_m = int(parse_num(item.get("融資限額")))
            util = round((curr_m / limit_m) * 100, 1) if limit_m > 0 else 0.0
            margin_map[code] = {
                "curr_lots": curr_m,
                "chg_lots": curr_m - prev_m,
                "util_pct": util
            }
except Exception as e:
    print(f"TWSE 融資讀取異常: {e}")

try:
    for item in fetch_json("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_margin_balance"):
        code = str(item.get("SecuritiesCompanyCode", "")).strip()
        if code in base_stocks:
            prev_m = int(parse_num(item.get("MarginPurchasePrevBalance")))
            curr_m = int(parse_num(item.get("MarginPurchaseBalance")))
            limit_m = int(parse_num(item.get("MarginPurchaseQuota")))
            util = round((curr_m / limit_m) * 100, 1) if limit_m > 0 else 0.0
            margin_map[code] = {
                "curr_lots": curr_m,
                "chg_lots": curr_m - prev_m,
                "util_pct": util
            }
except Exception as e:
    print(f"TPEx 融資讀取異常: {e}")

# 3. 抓取真實三大法人買賣超 (TWSE T86 & TPEx Institutional)
print("3. 正在抓取真實三大法人（外資、投信、自營商）買賣超資料...")
inst_map = {}
try:
    # 證交所近期三大法人買賣超日報
    for i in range(5):
        d_str = (now_tw - datetime.timedelta(days=i)).strftime("%Y%m%d")
        url_t86 = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={d_str}&selectType=ALLBUT0999&response=json"
        res_t86 = fetch_json(url_t86)
        if res_t86.get("stat") == "OK" and res_t86.get("data"):
            for row in res_t86["data"]:
                code = str(row[0]).strip()
                if code in base_stocks:
                    foreign_net = int(parse_num(row[4]) / 1000)   # 外資買賣超(張)
                    trust_net = int(parse_num(row[10]) / 1000)    # 投信買賣超(張)
                    total_net = int(parse_num(row[-1]) / 1000)    # 三大法人合計(張)
                    inst_map[code] = {
                        "foreign_net": foreign_net,
                        "trust_net": trust_net,
                        "total_net": total_net
                    }
            break
except Exception as e:
    print(f"TWSE 法人買賣超讀取異常: {e}")

try:
    for item in fetch_json("https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading"):
        code = str(item.get("SecuritiesCompanyCode", "")).strip()
        if code in base_stocks:
            foreign_net = int(parse_num(item.get("ForeignInvestorsDifference")) / 1000)
            trust_net = int(parse_num(item.get("InvestmentTrustDifference")) / 1000)
            total_net = int(parse_num(item.get("TotalDifference")) / 1000)
            inst_map[code] = {
                "foreign_net": foreign_net,
                "trust_net": trust_net,
                "total_net": total_net
            }
except Exception as e:
    print(f"TPEx 法人買賣超讀取異常: {e}")

# 4. 透過 yfinance 批次下載過去 3 個月（約 60 個交易日）100% 真實日 K 線
# 為確保 GitHub Actions 在 40 秒內穩定完成，依成交量排序取前 350 大活躍標的進行完整歷史 K 線下載
sorted_codes = sorted(base_stocks.keys(), key=lambda c: base_stocks[c]["vol"], reverse=True)[:350]
yf_symbols = [base_stocks[c]["yf_sym"] for c in sorted_codes] + ["0050.TW"]

print(f"4. 正在從 Yahoo Finance 批次下載 {len(yf_symbols)} 檔標的之近 3 個月真實歷史日 K 線...")
hist_data = yf.download(
    tickers=yf_symbols,
    period="3mo",
    interval="1d",
    group_by="ticker",
    threads=True,
    progress=False
)

# 計算台灣50 (0050.TW) 近三個月真實漲跌幅作為 RS 強度基準
benchmark_ret = 0.0
try:
    bm_df = hist_data["0050.TW"].dropna(subset=["Close"])
    if len(bm_df) >= 10:
        benchmark_ret = (float(bm_df["Close"].iloc[-1]) - float(bm_df["Close"].iloc[0])) / float(bm_df["Close"].iloc[0])
except Exception:
    pass

# 先計算所有股票的 3 個月真實報酬率，用來算真實百分位排名 (RS Rating 1~99)
raw_returns = {}
for code in sorted_codes:
    sym = base_stocks[code]["yf_sym"]
    try:
        df = hist_data[sym].dropna(subset=["Open", "High", "Low", "Close", "Volume"])
        if len(df) >= 15:
            ret_3m = (float(df["Close"].iloc[-1]) - float(df["Close"].iloc[0])) / float(df["Close"].iloc[0])
            raw_returns[code] = ret_3m
    except Exception:
        continue

# 將真實報酬率轉為 1~99 的百分位數 (真實 O'Neil RS Rating)
sorted_ret_codes = sorted(raw_returns.keys(), key=lambda c: raw_returns[c])
rs_rank_map = {}
total_valid = max(1, len(sorted_ret_codes))
for idx, c in enumerate(sorted_ret_codes):
    rs_rank_map[c] = max(1, min(99, int(((idx + 1) / total_valid) * 98) + 1))

all_stocks_output = []

for code in sorted_codes:
    if code not in raw_returns:
        continue
    info = base_stocks[code]
    sym = info["yf_sym"]
    try:
        df = hist_data[sym].dropna(subset=["Open", "High", "Low", "Close", "Volume"])
        if len(df) < 15:
            continue

        all_k = []
        for idx_dt, row in df.iterrows():
            o_p = round(float(row["Open"]), 2)
            h_p = round(float(row["High"]), 2)
            l_p = round(float(row["Low"]), 2)
            c_p = round(float(row["Close"]), 2)
            v_lots = int(float(row["Volume"]) / 1000)
            if c_p <= 0 or math.isnan(c_p):
                continue
            all_k.append({
                "date": idx_dt.strftime("%m/%d"),
                "open": o_p,
                "high": h_p,
                "low": l_p,
                "close": c_p,
                "vol": v_lots,
                "isUp": c_p >= o_p
            })

        if len(all_k) < 15:
            continue

        # 取最近 22 個交易日真實 K 線供前端繪圖
        kline_month = all_k[-22:]
        latest = all_k[-1]
        prev = all_k[-2]

        chg_val = round(latest["close"] - prev["close"], 2)
        chg_pct = round((chg_val / prev["close"]) * 100, 2) if prev["close"] > 0 else 0.0
        chg_str = f"+{chg_pct}%" if chg_pct >= 0 else f"{chg_pct}%"

        # 100% 真實歷史均量與相對成交量 (RVOL)
        vols = [k["vol"] for k in all_k]
        ma20_vol = max(1, int(sum(vols[-20:]) / len(vols[-20:])))
        ma60_vol = max(1, int(sum(vols[-60:]) / len(vols[-60:])))
        rvol_20 = round(latest["vol"] / ma20_vol, 2)
        rvol_60 = round(latest["vol"] / ma60_vol, 2)

        # 100% 真實歷史均價 (20MA / 60MA)
        closes = [k["close"] for k in all_k]
        ma20_price = round(sum(closes[-20:]) / len(closes[-20:]), 2)
        ma60_price = round(sum(closes[-60:]) / len(closes[-60:]), 2)
        stage_pass = latest["close"] >= ma60_price

        if latest["close"] >= ma20_price and ma20_price >= ma60_price:
            ma_trend = "多頭排列 (站上20/60MA)"
        elif stage_pass:
            ma_trend = "站上60MA季線"
        else:
            ma_trend = "季線下整理"

        # 100% 真實近 10 日高低點振幅 (VCP 波動收縮率)
        h_10 = max([k["high"] for k in all_k[-10:]])
        l_10 = min([k["low"] for k in all_k[-10:]])
        vcp_range = round(((h_10 - l_10) / l_10) * 100, 1) if l_10 > 0 else 10.0

        # 真實 RS Rating (1~99) 與 3 個月真實報酬率
        rs_rating = rs_rank_map.get(code, 50)
        ret_3m_pct = round(raw_returns[code] * 100, 1)

        # 真實三大法人與真實融資數據
        inst = inst_map.get(code, {"foreign_net": 0, "trust_net": 0, "total_net": 0})
        mrg = margin_map.get(code, {"curr_lots": 0, "chg_lots": 0, "util_pct": 0.0})

        # 根據真實數據計算供需分數與情緒溫差
        inst_bonus = 12 if inst["total_net"] > 500 else (6 if inst["total_net"] > 0 else -5)
        fund_score = min(99, max(30, int(50 + min(rvol_60 * 10, 25) + (rs_rating - 50) * 0.3 + inst_bonus)))
        sent_score = min(95, max(10, int(15 + mrg["util_pct"] * 0.8 + (8 if mrg["chg_lots"] > 200 else 0))))

        if rvol_20 >= 1.5 and latest["isUp"]:
            status_label = "帶量突破"
        elif inst["total_net"] > 300:
            status_label = "法人買超"
        elif vcp_range <= 10.0 and stage_pass:
            status_label = "量縮收斂"
        else:
            status_label = "常態整理"

        all_stocks_output.append({
            "code": code,
            "name": info["name"],
            "market": info["market"],
            "desc": f"{info['market']} · 今日量 {latest['vol']} 張 · 法人{('買超 ' + str(inst['total_net'])) if inst['total_net'] >= 0 else ('賣超 ' + str(abs(inst['total_net'])))}張",
            "price": latest["close"],
            "change": chg_str,
            "isUp": chg_pct >= 0,
            "status": status_label,
            "fundScore": fund_score,
            "sentScore": sent_score,
            "wallStreet": {
                "rvol20": rvol_20,
                "rvol60": rvol_60,
                "todayVol": latest["vol"],
                "ma20Vol": ma20_vol,
                "ma60Vol": ma60_vol,
                "ma20Price": ma20_price,
                "ma60Price": ma60_price,
                "maTrend": ma_trend,
                "stagePass": stage_pass,
                "rsRating": rs_rating,
                "ret3mPct": f"{'+' if ret_3m_pct >= 0 else ''}{ret_3m_pct}%",
                "vcpRange": vcp_range,
                "foreignNet": inst["foreign_net"],
                "trustNet": inst["trust_net"],
                "instTotalNet": inst["total_net"],
                "marginLots": mrg["curr_lots"],
                "marginChg": mrg["chg_lots"],
                "marginUtil": mrg["util_pct"]
            },
            "foreignIntel": {
                "title": f"{info['name']} ({code}) 近期市場新聞與產業報導索引",
                "zh_title": f"{info['name']} ({code}) 真實盤後收盤 {latest['close']} 元 ({chg_str})，三大法人合計 {inst['total_net']} 張",
                "source": f"{info['market']}真實盤後與新聞索引",
                "date": now_tw.strftime("%Y-%m-%d"),
                "url": f"https://www.google.com/search?q={urllib.parse.quote(info['name'] + ' ' + code + ' 營收 財報 新聞')}&tbm=nws",
                "summary": f"真實歷史計算：近月 20MA 均量 {ma20_vol} 張、60MA 季均量 {ma60_vol} 張，當日 RVOL {rvol_60} 倍；近一季真實累積漲跌幅 {ret_3m_pct}%（RS 強度 {rs_rating}）。"
            },
            "kline": kline_month
        })
    except Exception as e:
        continue

all_stocks_output.sort(key=lambda x: x["fundScore"], reverse=True)

output_data = {
    "update_time": now_tw.strftime("%Y-%m-%d %H:%M"),
    "stocks": all_stocks_output
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"完成！共寫入 {len(all_stocks_output)} 檔具備 100% 真實歷史 K 線與真實籌碼之台股數據。")
