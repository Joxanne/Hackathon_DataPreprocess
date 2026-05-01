import urllib.request, ssl, json

def main():
    print("=== [02_parking_taipei.py] 台北市停車場即時車位 ===")
    # 靜態資料（停車場基本資訊）
    static_url = "https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_alldesc.json"
    # 動態資料（即時剩餘車位）
    live_url   = "https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_allavailable.json"

    ctx = ssl._create_unverified_context()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    try:
        # 1. 先取靜態基本資訊 (用以取得名稱與總車位)
        req_static = urllib.request.Request(static_url, headers=headers)
        res_static = urllib.request.urlopen(req_static, context=ctx, timeout=15).read()
        static_data = json.loads(res_static.decode('utf-8-sig'))
        
        if isinstance(static_data, dict) and 'data' in static_data and 'park' in static_data['data']:
            s_parks = static_data['data']['park']
        elif isinstance(static_data, dict):
            s_parks = static_data.get('data', static_data.get('park', []))
        else:
            s_parks = static_data
            
        print(f"[成功] 取得靜態資料：共 {len(s_parks)} 筆停車場")
        
        # 建立查表字典
        park_info_map = {}
        for p in s_parks:
            pid = p.get('id', p.get('Id'))
            if pid:
                park_info_map[pid] = {
                    'name': p.get('name', p.get('Name', '?')),
                    'total': p.get('totalcar', "?")
                }

        # 2. 取即時車位
        req_live = urllib.request.Request(live_url, headers=headers)
        res_live = urllib.request.urlopen(req_live, context=ctx, timeout=15).read()
        live_data = json.loads(res_live.decode('utf-8-sig'))  # BOM-safe

        if isinstance(live_data, dict) and 'data' in live_data and 'park' in live_data['data']:
            parks = live_data['data']['park']
        elif isinstance(live_data, dict):
            parks = live_data.get('data', live_data.get('park', []))
        else:
            parks = live_data

        print(f"[成功] 取得即時車位資料：共 {len(parks)} 筆停車位更新")

        # 顯示前 5 筆合併資訊
        print("\n--- 即時剩餘車位示例（前 5 筆） ---")
        for p in parks[:5]:
            pid = p.get('id', p.get('Id', '?'))
            avail = p.get('availablecar', "?")
            
            # 從靜態表查名稱與總車位
            p_info = park_info_map.get(pid, {'name': '未知名稱', 'total': '?'})
            
            print(f"  [{pid}] {p_info['name']}: 剩餘 {avail} / 總 {p_info['total']} 格")

    except Exception as e:
        print("[失敗]", e)

if __name__ == '__main__':
    main()
