import urllib.request, ssl, json

def main():
    print("=== [01_youbike_taipei.py] YouBike 2.0 台北即時站點資訊 ===")
    # 官方 Open Data JSON（1分鐘更新，無需 API Key，完全公開）
    url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        res = urllib.request.urlopen(req, context=ctx, timeout=15).read()
        data = json.loads(res.decode('utf-8'))

        total = len(data)
        active = [s for s in data if s.get('act') == '1']
        print(f"[成功] 共取得 {total} 筆站點資料，其中啟用站點 {len(active)} 個")

        # 顯示前 5 筆站點
        print("\n--- 站點資料示例（前 5 筆） ---")
        for s in data[:5]:
            sno = s.get('sno', '?')
            name = s.get('sna', '?')
            area = s.get('sarea', '?')
            rent = s.get('available_rent_bikes', 0)
            ret = s.get('available_return_bikes', 0)
            total_slots = s.get('Quantity', 0)
            lat = s.get('latitude', 0)
            lng = s.get('longitude', 0)
            updated = s.get('infoTime', '?')
            print(f"  [{sno}] {area} {name}")
            print(f"    可借: {rent} 輛 | 可還: {ret} 格 | 總格位: {total_slots}")
            print(f"    座標: ({lat}, {lng}) | 更新: {updated}")

        # 統計低庫存預警（可借 <= 2）
        low_stock = [s for s in active if s.get('available_rent_bikes', 99) <= 2]
        print(f"\n⚠️ 低庫存預警（可借 ≤ 2 輛）：{len(low_stock)} 站")
        for s in low_stock[:5]:
            print(f"  {s.get('sarea')} {s.get('sna')}: 可借 {s.get('available_rent_bikes')} 輛")

    except Exception as e:
        print("[失敗]", e)

if __name__ == '__main__':
    main()
