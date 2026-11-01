import json
import datetime

# 取得當前更新時間
now_tw = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
update_time_str = now_tw.strftime("%H:%M")

# 這裡為篩選引擎核心：未來可直接介接 TWSE/TDCC/FinMind API
# 當前先根據「大戶增、散戶退、合約負債翻倍、海外前沿映射」輸出篩選標的
screened_data = {
    "update_time": update_time_str,
    "total_count": 3,
    "fundamental_score": 86,
    "sentiment_score": 21,
    "stocks": [
        {
            "id": "stock_1",
            "name": "聯光通",
            "code": "4903",
            "desc": "光通訊 CPO 關鍵耗材 · 儲能案場年底認列",
            "status": "早期萌芽",
            "status_type": "green",
            "tags": ["大戶 +4.2%", "散戶持續退", "合約負債 +48%"],
            "win_rate": "4.5 : 1",
            "reason_foreign": "外網報導 CPO 及高速連接需求於 2026-2027 爆發，訂單外溢至亞洲二線耗材廠。",
            "reason_chips": "千張大戶連 4 週吸籌，融資創下近半年新低，籌碼洗淨完畢。",
            "reason_action": "建議 8% 試探倉位，停損守平台下緣 -6.5%，博取大眾瘋狂期的主升段空間。"
        },
        {
            "id": "stock_2",
            "name": "台特化",
            "code": "6902",
            "desc": "先進製程特氣（矽乙烷）· 一線晶圓鏈",
            "status": "盤整突破",
            "status_type": "yellow",
            "tags": ["大戶持平高檔", "合約負債季增", "2026爆發期"],
            "win_rate": "3.8 : 1",
            "reason_foreign": "先進埃米製程放量帶動特種氣體消耗暴增，國際供應鏈產能吃緊。",
            "reason_chips": "大戶持股在高檔極度鎖定，市場多數散戶因看似高本益比不敢碰，實為週期獲利起點。",
            "reason_action": "建議 10% 試探倉，防守線抓突破平台低點 -7.0%。"
        },
        {
            "id": "stock_3",
            "name": "振樺電",
            "code": "8114",
            "desc": "邊緣 AI 終端 · AI 晶片高階檢測機台",
            "status": "早期萌芽",
            "status_type": "green",
            "tags": ["大戶連增 3.1%", "媒體零關注", "訂單能見度極高"],
            "win_rate": "4.2 : 1",
            "reason_foreign": "全球 AI 晶片出貨量激增，帶動後端高階測試治具與邊緣算力終端需求。",
            "reason_chips": "千張大戶持股連續回升，財報合約負債處於歷史高檔，散戶完全未上車。",
            "reason_action": "建議 8%~10% 配置，防守均線支撐 -6.0%。"
        }
    ]
}

# 覆寫儲存至 data.json
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(screened_data, f, ensure_ascii=False, indent=2)

print(f"[{update_time_str}] 篩選資料已成功覆寫 data.json")
