import urllib.request, ssl, json

def main():
    print("=== [06_water_ntpc.py] 停水、降壓相關警示 (台水 Open Data API) ===")
    # 台灣自來水公司提供的開放資料 JSON API（新北市轄區停水公告）
    # 官方 Open Data JSON: https://web.water.gov.tw/wateroffapi/openData/export/json
    url = "https://web.water.gov.tw/wateroffapi/openData/export/json"
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*'
        })
        res = urllib.request.urlopen(req, context=ctx, timeout=15).read()
        data = json.loads(res.decode('utf-8'))

        if not data:
            print("[成功] 目前無停水/降壓公告。")
            return

        # 篩選新北市相關公告
        ntpc_records = [r for r in data if '新北' in str(r.get('AffectedCounty', '')) or
                                          '新北' in str(r.get('affected_county', '')) or
                                          '新北' in str(r)]
        print(f"[成功] 取得 {len(data)} 筆全台停水資料，其中新北市相關: {len(ntpc_records)} 筆")

        if ntpc_records:
            print("\n--- 新北市停水/降壓公告 ---")
            for r in ntpc_records[:5]:
                print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print("\n[新北市] 目前無停水/降壓公告。")
            print(f"\n--- 全台最新前3筆停水公告 ---")
            for r in data[:3]:
                print(json.dumps(r, ensure_ascii=False, indent=2))

    except Exception as e:
        print("[失敗]", e)
        print("[備用] 請至 https://web.water.gov.tw/wateroff/city/新北市/index.html 手動查詢")

if __name__ == '__main__':
    main()
