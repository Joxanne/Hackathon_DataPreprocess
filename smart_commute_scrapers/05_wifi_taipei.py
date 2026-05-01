"""
05_wifi_taipei.py - TaipeiFree WiFi 熱點位置（靜態，6個月更新一次）
資料來源: data.taipei（臺北市資料大平臺）
格式: CSV，直接下載，無需 API Key
"""
import urllib.request, ssl, csv, io

def main():
    print("=== [05_wifi_taipei.py] TaipeiFree WiFi 熱點位置 ===")
    url = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=549b3a9b-eb6c-4cb1-848b-8c238735e2db"
    ctx = ssl._create_unverified_context()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, context=ctx, timeout=20)
        raw = res.read()
        # 嘗試多種編碼
        for enc in ('utf-8-sig', 'utf-8', 'big5', 'cp950'):
            try:
                text = raw.decode(enc)
                break
            except:
                continue

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        print(f"[成功] 共取得 {len(rows)} 筆 WiFi 熱點")

        if rows:
            print("欄位:", list(rows[0].keys()))
            print("\n--- 前 3 筆熱點 ---")
            for r in rows[:3]:
                site_id = r.get('SITE_ID', '?')
                name    = r.get('NAME', r.get('E_NAME', '?'))
                addr    = r.get('ADDR', r.get('E_ADDR', '?'))
                lat     = r.get('LATITUDE', '?')
                lon     = r.get('LONGITUDE', '?')
                area    = r.get('AREA', '?')
                print(f"  [{site_id}] {name}")
                print(f"    地點: {area} {addr}")
                print(f"    座標: ({lat}, {lon})")

    except Exception as e:
        print("[失敗]", e)

if __name__ == '__main__':
    main()
