"""
06_rainfall_cwa.py - 即時雨量站資料（氣象署，10分鐘更新）
資料來源: opendata.cwa.gov.tw（中央氣象署開放資料平台）
需要: 免費 API Key（可至 opendata.cwa.gov.tw 申請，共用基礎層已有 Key）
"""
import urllib.request, ssl, json

CWA_KEY = "CWA-098BE5E3-2529-46C2-A82E-F996D8BA9D98"

def main():
    print("=== [06_rainfall_cwa.py] 即時雨量站資料（氣象署）===")
    # O-A0002-001: 雨量站即時觀測資料
    url = (f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001"
           f"?Authorization={CWA_KEY}&format=JSON&limit=5")
    ctx = ssl._create_unverified_context()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        data = json.loads(res.read().decode('utf-8'))

        stations = data.get('records', {}).get('Station', [])
        print(f"[成功] 共取得 {len(stations)} 筆雨量站資料")

        print("\n--- 前 3 站即時雨量 ---")
        for s in stations[:3]:
            name   = s.get('StationName', '?')
            sid    = s.get('StationId', '?')
            county = s.get('GeoInfo', {}).get('CountyName', '?')
            town   = s.get('GeoInfo', {}).get('TownName', '?')
            obs    = s.get('ObsTime', {}).get('DateTime', '?')
            rain   = s.get('RainfallElement', {})
            now_r  = rain.get('Now', {}).get('Precipitation', '?')
            hr1_r  = rain.get('Past1hr', {}).get('Precipitation', '?')
            hr24_r = rain.get('Past24hr', {}).get('Precipitation', '?')

            print(f"  [{sid}] {county} {town} {name}")
            print(f"    觀測時間: {obs}")
            print(f"    即時雨量: {now_r} mm | 過去1小時: {hr1_r} mm | 過去24小時: {hr24_r} mm")

    except Exception as e:
        print("[失敗]", e)

if __name__ == '__main__':
    main()
