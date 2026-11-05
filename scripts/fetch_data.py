import json
import datetime
import urllib.request
import urllib.parse
import ssl
import math
import yfinance as yf

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

now_tw = datetime.datetime.utcnow() + datetime.timedelta(hours=8)


def parse_num(val):
    if val is None:
        return None
    s = str(val).replace(",", "").replace("+", "").replace("X", "").strip()
    if s in ["", "--", "---", "----", "N/A"]:
        return None
    try:
        return float(s)
    except Exception:
        return None


def fetch_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
        return json.loads(resp.read().decode('utf-8'))


print("1. 讀取證交所與櫃買中心當日全市場收盤行情...")
base_stocks = {}

# 上市當日行情 (TWSE)
try:
    for item in fetch_json("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"):
        code = str(item.get("Code", "")).strip()
        if len(code) == 4 and code.isdigit():
            close_p = parse_num(item.get("ClosingPrice"))
            vol_shares = parse_num(item.get("TradeVolume"))
            if close_p and vol_shares and close_p >= 10.0 and (vol_shares / 1000) >= 500:
                base_stocks[code] = {
                    "code": code,
                    "name": str(item.get("Name", "")).strip(),
                    "market": "上市",
                    "yf_sym": f"{code}.TW",
                    "vol": int(vol_shares / 1000)
                }
except Exception as e:
    print(f"TWSE 讀取異常: {e}")

# 上櫃當日行情 (TPEx)
try:
    for item in fetch_json("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"):
        code = str(item.get("SecuritiesCompanyCode", "")).strip()
        if len(code) == 4 and code.isdigit():
            close_p = parse_num(item.get("Close"))
            vol_shares = parse_num(item.get("TradingShares"))
            if close_p and vol_shares and close_p >= 10.0 and (vol_shares / 1000) >= 500:
                base_stocks[code] = {
                    "code": code,
                    "name": str(item.get("CompanyName", "")).strip(),
                    "market": "上櫃",
                    "yf_sym": f"{code}.TWO",
                    "vol": int(vol_shares / 1000)
                }
except Exception as e:
    print(f"TPEx 讀取異常: {e}")

print(f"共取得 {len(base_stocks)} 檔當日成交量 >= 500 張之普通股。")

# 2. 讀取官方融資餘額 (TWSE & TPEx)
margin_map = {}
try:
    for item in fetch_json("https://openapi.twse.com.tw/v1/exchangeReport/MI_MARGN"):
        code = str(item.get("股票代號", "")).strip()
        if code in base_stocks:
            prev_m = parse_num(item.get("融資前日餘額"))
            curr_m = parse_num(item.get("融資今日餘額"))
            limit_m = parse_num(item.get("融資限額"))
            if curr_m is not None and prev_m is not None:
                util = round((curr_m / limit_m) * 100, 1) if (limit_m and limit_m > 0) else 0.0
                margin_map[code] = {
                    "curr_lots": int(curr_m),
                    "chg_lots": int(curr_m - prev_m),
                    "util_pct": util
                }
except Exception as e:
    print(f"TWSE 融資讀取異常: {e}")

try:
    for item in fetch_json("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_margin_balance"):
        code = str(item.get("SecuritiesCompanyCode", "")).strip()
        if code in base_stocks:
            prev_m = parse_num(item.get("MarginPurchasePrevBalance"))
            curr_m = parse_num(item.get("MarginPurchaseBalance"))
            limit_m = parse_num(item.get("MarginPurchaseQuota"))
            if curr_m is not None and prev_m is not None:
                util = round((curr_m / limit_m) * 100, 1) if (limit_m and limit_m > 0) else 0.0
                margin_map[code] = {
                    "curr_lots": int(curr_m),
                    "chg_lots": int(curr_m - prev_m),
                    "util_pct": util
                }
except Exception as e:
    print(f"TPEx 融資讀取異常: {e}")

# 3. 依成交量取前 350 檔活躍股，批次下載過去 3 個月真實歷史日 K 線
sorted_codes = sorted(base_stocks.keys(), key=lambda c: base_stocks[c]["vol"], reverse=True)[:350]
yf_symbols = [base_stocks[c]["yf_sym"] for c in sorted_codes]

print(f"正在下載 {len(yf_symbols)} 檔股票過去 3 個月真實歷史日 K 線...")
hist_data = yf.download(
    tickers=yf_symbols,
    period="3mo",
    interval="1d",
    group_by="ticker",
    threads=True,
    progress=False
)

# 計算每檔股票過去 3 個月真實累積漲跌幅與 RS 百分位排名
raw_returns = {}
valid_k_map = {}

for code in sorted_codes:
    sym = base_stocks[code]["yf_sym"]
    try:
        df = hist_data[sym].dropna(subset=["Open", "High", "Low", "Close", "Volume"])
        if len(df) < 20:
            continue
        k_list = []
        for idx_dt, row in df.iterrows():
            o_p = round(float(row["Open"]), 2)
            h_p = round(float(row["High"]), 2)
            l_p = round(float(row["Low"]), 2)
            c_p = round(float(row["Close"]), 2)
            v_lots = int(float(row["Volume"]) / 1000)
            if c_p <= 0 or math.isnan(c_p):
                continue
            k_list.append({
                "date": idx_dt.strftime("%m/%d"),
                "open": o_p,
                "high": h_p,
                "low": l_p,
                "close": c_p,
                "vol": v_lots,
                "isUp": c_p >= o_p
            })
        if len(k_list) >= 20 and k_list[0]["close"] > 0:
            valid_k_map[code] = k_list
            raw_returns[code] = (k_list[-1]["close"] - k_list[0]["close"]) / k_list[0]["close"]
    except Exception:
        continue

sorted_ret_codes = sorted(raw_returns.keys(), key=lambda c: raw_returns[c])
rs_rank_map = {}
total_valid = max(1, len(sorted_ret_codes))
for idx, c in enumerate(sorted_ret_codes):
    rs_rank_map[c] = max(1, min(99, int(((idx + 1) / total_valid) * 98) + 1))

stocks_output = []

for code, all_k in valid_k_map.items():
    info = base_stocks[code]
    latest = all_k[-1]
    prev = all_k[-2]

    chg_val = round(latest["close"] - prev["close"], 2)
    chg_pct = round((chg_val / prev["close"]) * 100, 2) if prev["close"] > 0 else 0.0
    chg_str = f"+{chg_pct}%" if chg_pct >= 0 else f"{chg_pct}%"

    # 真實歷史均量與 RVOL
    vols = [k["vol"] for k in all_k]
    ma20_vol = max(1, int(sum(vols[-20:]) / len(vols[-20:])))
    ma60_vol = max(1, int(sum(vols[-60:]) / len(vols[-60:])))
    rvol_20 = round(latest["vol"] / ma20_vol, 2)
    rvol_60 = round(latest["vol"] / ma60_vol, 2)

    # 真實歷史均價 (20MA / 60MA)
    closes = [k["close"] for k in all_k]
    ma20_price = round(sum(closes[-20:]) / len(closes[-20:]), 2)
    ma60_price = round(sum(closes[-60:]) / len(closes[-60:]), 2)
    above_ma20 = latest["close"] >= ma20_price
    above_ma60 = latest["close"] >= ma60_price

    if above_ma20 and ma20_price >= ma60_price:
        ma_trend = "站上20/60MA"
    elif above_ma60:
        ma_trend = "站上60MA季線"
    else:
        ma_trend = "60MA季線之下"

    # 真實近 10 日高低振幅 (%)
    h_10 = max([k["high"] for k in all_k[-10:]])
    l_10 = min([k["low"] for k in all_k[-10:]])
    vcp_range = round(((h_10 - l_10) / l_10) * 100, 1) if l_10 > 0 else 0.0

    # 真實近 20 日與近一季累積漲跌幅 (%)
    close_20d_ago = all_k[-20]["close"]
    ret_20d_pct = round(((latest["close"] - close_20d_ago) / close_20d_ago) * 100, 1) if close_20d_ago > 0 else 0.0
    ret_3m_pct = round(raw_returns[code] * 100, 1)
    rs_rating = rs_rank_map.get(code, 50)

    mrg = margin_map.get(code)

    if rvol_20 >= 1.5 and latest["isUp"]:
        status_label = "放量上漲"
    elif above_ma20 and above_ma60:
        status_label = "均線多頭"
    else:
        status_label = "區間整理"

    stocks_output.append({
        "code": code,
        "name": info["name"],
        "market": info["market"],
        "desc": f"{info['market']} · 當日量 {latest['vol']} 張 · 20日均量 {ma20_vol} 張",
        "price": latest["close"],
        "change": chg_str,
        "chgPct": chg_pct,
        "isUp": chg_pct >= 0,
        "status": status_label,
        "metrics": {
            "todayVol": latest["vol"],
            "ma20Vol": ma20_vol,
            "ma60Vol": ma60_vol,
            "rvol20": rvol_20,
            "rvol60": rvol_60,
            "ma20Price": ma20_price,
            "ma60Price": ma60_price,
            "aboveMa20": above_ma20,
            "aboveMa60": above_ma60,
            "maTrend": ma_trend,
            "rsRating": rs_rating,
            "ret20dPct": ret_20d_pct,
            "ret3mPct": ret_3m_pct,
            "vcpRange": vcp_range,
            "marginLots": mrg["curr_lots"] if mrg else None,
            "marginChg": mrg["chg_lots"] if mrg else None,
            "marginUtil": mrg["util_pct"] if mrg else None
        },
        "newsUrl": f"https://www.google.com/search?q={urllib.parse.quote(info['name'] + ' ' + code + ' 股票 新聞')}&tbm=nws",
        "kline": all_k[-22:]
    })

# 預設依 60日相對量能 (RVOL) 由高至低排序
stocks_output.sort(key=lambda x: x["metrics"]["rvol60"], reverse=True)

output_data = {
    "update_time": now_tw.strftime("%Y-%m-%d %H:%M"),
    "stocks": stocks_output
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"完成！共寫入 {len(stocks_output)} 檔 100% 真實歷史計算之台股數據。")
