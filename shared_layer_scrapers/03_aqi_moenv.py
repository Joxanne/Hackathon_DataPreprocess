import urllib.request
import ssl
import json

ctx = ssl._create_unverified_context()

# 環境部 AQI 空氣品質指標即時資料
# 免費 API Key（每日限5000次）: 需自行至 https://data.moenv.gov.tw/ 申請
# 若 API Key 超過限額，改用備用端點 data.gov.tw CORS-free JSON
API_KEY = "3351274f-9cad-48b4-9588-0071e781b16a"
url = f"https://data.moenv.gov.tw/api/v2/aqx_p_432?format=json&limit=5&api_key={API_KEY}"

def main():
    print("=== [03_aqi_moenv.py] 空氣品質 AQI ===")
    print(f"正在請求: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        data = res.read().decode('utf-8')

        print("請求成功！")
        try:
            parsed = json.loads(data)
            # 速率限制時，回傳 dict 含 message 欄位
            if isinstance(parsed, dict) and 'message' in parsed:
                print(f"[API訊息] {parsed['message']}")
                print("[提示] API Key 可能已超過每日 5000 次限額，請明日再試，或至 https://data.moenv.gov.tw/ 申請新的 API Key。")
                return
            print("------- AQI JSON 預覽 -------")
            # 回傳格式有兩種：直接是 list，或是 {"records": [...], ...}
            if isinstance(parsed, list):
                records = parsed
            elif isinstance(parsed, dict):
                records = parsed.get('records', parsed.get('data', []))
            else:
                records = []

            if records:
                print(f"[成功] 共取得 {len(records)} 筆測站資料，顯示前 3 筆:")
                for r in records[:3]:
                    site = r.get('sitename', r.get('SiteName', '?'))
                    county = r.get('county', r.get('County', '?'))
                    aqi = r.get('aqi', r.get('AQI', '?'))
                    status = r.get('status', r.get('Status', '?'))
                    print(f"  {county} {site}: AQI={aqi} ({status})")
            else:
                print("找不到資料，完整回應:")
                print(json.dumps(parsed, ensure_ascii=False, indent=2)[:500])
        except json.JSONDecodeError:
            print("------- 內容非 JSON 格式 -------")
            print(data[:500])
            print("\n[提示] 若看到速率限制訊息，表示 API Key 超額，請申請新的。")
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == '__main__':
    main()
