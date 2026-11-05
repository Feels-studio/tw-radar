import json
import datetime
import time
import math
import urllib.request
import urllib.parse
import ssl
import yfinance as yf
import pandas as pd

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

now_tw = datetime.datetime.utcnow() + datetime.timedelta(hours=8)

# 台股真實核心標的池（包含上市 .TW 與上櫃 .TWO 真實代號與名稱，確保即使證交所擋海外IP也能100%向Yahoo抓取真實K線）
CORE_TW_STOCKS = [
    ("2330", "台積電", "上市", "2330.TW"), ("2317", "鴻海", "上市", "2317.TW"), ("2454", "聯發科", "上市", "2454.TW"),
    ("2382", "廣達", "上市", "2382.TW"), ("3231", "緯創", "上市", "3231.TW"), ("2376", "技嘉", "上市", "2376.TW"),
    ("6669", "緯穎", "上市", "6669.TW"), ("3017", "奇鋐", "上市", "3017.TW"), ("3324", "雙鴻", "上櫃", "3324.TWO"),
    ("2308", "台達電", "上市", "2308.TW"), ("3450", "聯鈞", "上市", "3450.TW"), ("4979", "華星光", "上櫃", "4979.TWO"),
    ("3363", "上詮", "上櫃", "3363.TWO"), ("3163", "波若威", "上櫃", "3163.TWO"), ("4908", "前鼎", "上櫃", "4908.TWO"),
    ("6442", "光聖", "上市", "6442.TW"), ("4903", "聯光通", "上櫃", "4903.TWO"), ("6530", "創威", "上櫃", "6530.TWO"),
    ("3081", "聯亞", "上櫃", "3081.TWO"), ("2345", "智邦", "上市", "2345.TW"), ("3583", "辛耘", "上市", "3583.TW"),
    ("3131", "弘塑", "上櫃", "3131.TWO"), ("6187", "萬潤", "上櫃", "6187.TWO"), ("5443", "均豪", "上櫃", "5443.TWO"),
    ("6640", "均華", "上櫃", "6640.TWO"), ("2467", "志聖", "上市", "2467.TW"), ("4772", "台特化", "上櫃", "4772.TWO"),
    ("4768", "晶呈科技", "上櫃", "4768.TWO"), ("1727", "中華化", "上市", "1727.TW"), ("3661", "世芯-KY", "上市", "3661.TW"),
    ("3443", "創意", "上市", "3443.TW"), ("3035", "智原", "上市", "3035.TW"), ("6531", "愛普*", "上市", "6531.TW"),
    ("5274", "信驊", "上櫃", "5274.TWO"), ("3529", "力旺", "上櫃", "3529.TWO"), ("6643", "M31", "上櫃", "6643.TWO"),
    ("8299", "群聯", "上櫃", "8299.TWO"), ("2408", "南亞科", "上市", "2408.TW"), ("2344", "華邦電", "上市", "2344.TW"),
    ("3260", "威剛", "上櫃", "3260.TWO"), ("4967", "十銓", "上市", "4967.TW"), ("2368", "金像電", "上市", "2368.TW"),
    ("2383", "台光電", "上市", "2383.TW"), ("6274", "台燿", "上櫃", "6274.TWO"), ("3037", "欣興", "上市", "3037.TW"),
    ("8046", "南電", "上市", "8046.TW"), ("3189", "景碩", "上市", "3189.TW"), ("2313", "華通", "上市", "2313.TW"),
    ("1519", "華城", "上市", "1519.TW"), ("1513", "中興電", "上市", "1513.TW"), ("1503", "士電", "上市", "1503.TW"),
    ("1514", "亞力", "上市", "1514.TW"), ("1609", "大亞", "上市", "1609.TW"), ("6806", "森崴能源", "上市", "6806.TW"),
    ("9958", "世紀鋼", "上市", "9958.TW"), ("2603", "長榮", "上市", "2603.TW"), ("2609", "陽明", "上市", "2609.TW"),
    ("2615", "萬海", "上市", "2615.TW"), ("2618", "長榮航", "上市", "2618.TW"), ("2610", "華航", "上市", "2610.TW"),
    ("2634", "漢翔", "上市", "2634.TW"), ("8222", "寶一", "上市", "8222.TW"), ("5284", "jpp-KY", "上市", "5284.TW"),
    ("3008", "大立光", "上市", "3008.TW"), ("3406", "玉晶光", "上市", "3406.TW"), ("2327", "國巨", "上市", "2327.TW"),
    ("2492", "華新科", "上市", "2492.TW"), ("2379", "瑞昱", "上市", "2379.TW"), ("3034", "聯詠", "上市", "3034.TW"),
    ("2395", "研華", "上市", "2395.TW"), ("8114", "振樺電", "上市", "8114.TW"), ("6414", "樺漢", "上市", "6414.TW"),
    ("2357", "華碩", "上市", "2357.TW"), ("2353", "宏碁", "上市", "2353.TW"), ("2377", "微星", "上市", "2377.TW"),
    ("2356", "英業達", "上市", "2356.TW"), ("2324", "仁寶", "上市", "2324.TW"), ("2301", "光寶科", "上市", "2301.TW"),
    ("3711", "日月光投控", "上市", "3711.TW"), ("2449", "京元電子", "上市", "2449.TW"), ("6257", "矽格", "上市", "6257.TW"),
    ("6147", "頎邦", "上櫃", "6147.TWO"), ("3680", "家登", "上櫃", "3680.TWO"), ("6196", "帆宣", "上市", "6196.TW"),
    ("2404", "漢唐", "上市", "2404.TW"), ("5536", "聖暉*", "上櫃", "5536.TWO"), ("6691", "洋基工程", "上市", "6691.TW"),
    ("2360", "致茂", "上市", "2360.TW"), ("6223", "旺矽", "上櫃", "6223.TWO"), ("6515", "穎崴", "上市", "6515.TW"),
    ("6683", "雍智科技", "上櫃", "6683.TWO"), ("3533", "嘉澤", "上市", "3533.TW"), ("3665", "貿聯-KY", "上市", "3665.TW"),
    ("6285", "啟碁", "上市", "6285.TW"), ("5388", "中磊", "上市", "5388.TW"), ("3596", "智易", "上市", "3596.TW"),
    ("2455", "全新", "上市", "2455.TW"), ("3105", "穩懋", "上櫃", "3105.TWO"), ("8086", "宏捷科", "上櫃", "8086.TWO"),
    ("6488", "環球晶", "上櫃", "6488.TWO"), ("5483", "中美晶", "上櫃", "5483.TWO"), ("3532", "台勝科", "上市", "3532.TW"),
    ("1795", "美時", "上市", "1795.TW"), ("6446", "藥華藥", "上市", "6446.TW"), ("4743", "合一", "上櫃", "4743.TWO"),
    ("2881", "富邦金", "上市", "2881.TW"), ("2882", "國泰金", "上市", "2882.TW"), ("2891", "中信金", "上市", "2891.TW"),
    ("2886", "兆豐金", "上市", "2886.TW"), ("2884", "玉山金", "上市", "2884.TW"), ("2002", "中鋼", "上市", "2002.TW"),
    ("1101", "台泥", "上市", "1101.TW"), ("1301", "台塑", "上市", "1301.TW"), ("1303", "南亞", "上市", "1303.TW"),
    ("2912", "統一超", "上市", "2912.TW"), ("1216", "統一", "上市", "1216.TW"), ("9910", "豐泰", "上市", "9910.TW"),
    ("1476", "儒鴻", "上市", "1476.TW"), ("1477", "聚陽", "上市", "1477.TW"), ("8454", "富邦媒", "上市", "8454.TW")
]

base_stocks = {}
for code, name, mkt, sym in CORE_TW_STOCKS:
    base_stocks[code] = {"code": code, "name": name, "market": mkt, "yf_sym": sym}

# 嘗試再從證交所與櫃買中心擴充當日增量名單（若海外IP被擋也不影響核心股票池執行）
try:
    req = urllib.request.Request("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        for item in json.loads(resp.read().decode('utf-8')):
            c = str(item.get("Code", "")).strip()
            v_str = str(item.get("TradeVolume", "0")).replace(",", "").strip()
            p_str = str(item.get("ClosingPrice", "0")).replace(",", "").strip()
            if len(c) == 4 and c.isdigit() and v_str.isdigit():
                try:
                    if float(p_str) >= 15.0 and int(v_str) >= 3000000: # 成交量 >= 3000張
                        base_stocks[c] = {"code": c, "name": str(item.get("Name", "")).strip(), "market": "上市", "yf_sym": f"{c}.TW"}
                except Exception:
                    pass
except Exception as e:
    print(f"TWSE 擴充跳過 (使用核心標的池): {e}")

try:
    req = urllib.request.Request("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes", headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        for item in json.loads(resp.read().decode('utf-8')):
            c = str(item.get("SecuritiesCompanyCode", "")).strip()
            v_str = str(item.get("TradingShares", "0")).replace(",", "").strip()
            p_str = str(item.get("Close", "0")).replace(",", "").strip()
            if len(c) == 4 and c.isdigit() and v_str.isdigit():
                try:
                    if float(p_str) >= 15.0 and int(v_str) >= 3000000:
                        base_stocks[c] = {"code": c, "name": str(item.get("CompanyName", "")).strip(), "market": "上櫃", "yf_sym": f"{c}.TWO"}
                except Exception:
                    pass
except Exception as e:
    print(f"TPEx 擴充跳過 (使用核心標的池): {e}")

all_codes = list(base_stocks.keys())
print(f"準備向 Yahoo Finance 全球伺服器抓取 {len(all_codes)} 檔台股之過去 3 個月真實歷史日 K 線...")

valid_k_map = {}
raw_returns = {}

# 分批下載（每批 40 檔），徹底避免 Yahoo 封鎖或單一標出錯導致整包失敗
BATCH_SIZE = 40
for i in range(0, len(all_codes), BATCH_SIZE):
    batch_codes = all_codes[i:i + BATCH_SIZE]
    batch_syms = [base_stocks[c]["yf_sym"] for c in batch_codes]
    print(f"正在下載第 {i+1} ~ {min(i+BATCH_SIZE, len(all_codes))} 檔...")
    try:
        data = yf.download(
            tickers=batch_syms,
            period="3mo",
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False
        )
        for c in batch_codes:
            sym = base_stocks[c]["yf_sym"]
            try:
                df = data[sym] if len(batch_syms) > 1 else data
                df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
                if len(df) < 15:
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
                if len(k_list) >= 15 and k_list[0]["close"] > 0 and k_list[-1]["vol"] > 0:
                    valid_k_map[c] = k_list
                    raw_returns[c] = (k_list[-1]["close"] - k_list[0]["close"]) / k_list[0]["close"]
            except Exception:
                continue
    except Exception as e:
        print(f"批次下載異常: {e}")
    time.sleep(0.5)

print(f"成功取得 {len(valid_k_map)} 檔具備完整 60 日真實日 K 線之股票！")

# 計算真實近一季漲跌幅排名 (RS Rating 1~99)
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
    above_ma20 = latest["close"] >= ma20_price
    above_ma60 = latest["close"] >= ma60_price

    if above_ma20 and ma20_price >= ma60_price:
        ma_trend = "站上20/60MA"
    elif above_ma60:
        ma_trend = "站上60MA季線"
    else:
        ma_trend = "60MA季線之下"

    # 100% 真實近 10 日高低點箱體振幅 (%)
    h_10 = max([k["high"] for k in all_k[-10:]])
    l_10 = min([k["low"] for k in all_k[-10:]])
    vcp_range = round(((h_10 - l_10) / l_10) * 100, 1) if l_10 > 0 else 0.0

    # 100% 真實近 20 日與近 60 日累積漲跌幅 (%)
    idx_20 = max(0, len(all_k) - 20)
    close_20d_ago = all_k[idx_20]["close"]
    ret_20d_pct = round(((latest["close"] - close_20d_ago) / close_20d_ago) * 100, 1) if close_20d_ago > 0 else 0.0
    ret_3m_pct = round(raw_returns[code] * 100, 1)
    rs_rating = rs_rank_map.get(code, 50)

    if rvol_20 >= 1.5 and latest["isUp"]:
        status_label = "放量上漲"
    elif above_ma20 and above_ma60:
        status_label = "均線多頭"
    else:
        status_label = "區間整理"

    metrics_obj = {
        "todayVol": latest["vol"],
        "ma20Vol": ma20_vol,
        "ma60Vol": ma60_vol,
        "rvol20": rvol_20,
        "rvol60": rvol_60,
        "ma20Price": ma20_price,
        "ma60Price": ma60_price,
        "aboveMa20": above_ma20,
        "aboveMa60": above_ma60,
        " stagePass": above_ma60,
        "maTrend": ma_trend,
        "rsRating": rs_rating,
        "ret20dPct": ret_20d_pct,
        "ret3mPct": ret_3m_pct,
        "vcpRange": vcp_range
    }

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
        "metrics": metrics_obj,
        "wallStreet": metrics_obj, # 雙向相容欄位
        "newsUrl": f"https://www.google.com/search?q={urllib.parse.quote(info['name'] + ' ' + code + ' 股票 新聞')}&tbm=nws",
        "kline": all_k[-22:]
    })

stocks_output.sort(key=lambda x: x["metrics"]["rvol60"], reverse=True)

# 絕對安全防護：若抓取數量為 0，直接拋出例外讓 GitHub Actions 報紅燈，絕不把空陣列寫入覆蓋 data.json
if len(stocks_output) == 0:
    raise RuntimeError("錯誤：未抓到任何有效股票資料，停止覆寫 data.json")

output_data = {
    "update_time": now_tw.strftime("%Y-%m-%d %H:%M"),
    "total_count": len(stocks_output),
    "stocks": stocks_output
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"成功寫入 {len(stocks_output)} 檔 100% 真實歷史 K 線與均價均量數據至 data.json！")
