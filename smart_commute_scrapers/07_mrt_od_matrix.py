"""
07_mrt_od_matrix.py - 台北捷運各站分時 OD 流量統計（歷史月資料）
資料來源: data.taipei（臺北捷運公司提供，每月更新）
無需 API Key，CSV 直接下載
注意: 此為歷史統計，非即時資料
"""
import urllib.request, ssl, json, csv, io

def main():
    print("=== [07_mrt_od_matrix.py] 台北捷運分時 OD 流量統計（月資料） ===")
    # 資料集索引頁（回傳每個月份的 CSV 下載連結）
    index_url = ("https://data.taipei/api/v1/dataset/eb481f58-1238-4cff-8caa-fa7bb20cb4f4"
                 "?scope=resourceAquire&limit=5")
    ctx = ssl._create_unverified_context()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        req = urllib.request.Request(index_url, headers=headers)
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        idx = json.loads(res.read().decode('utf-8'))

        results = idx.get('result', {}).get('results', [])
        total   = idx.get('result', {}).get('count', 0)
        print(f"[成功] 共有 {total} 個月份的 OD 矩陣資料集")
        print("\n最新幾個月份的下載連結:")
        for r in results[-3:]:
            yr  = r.get('年份', r.get('seqno', '?'))
            mo  = r.get('月', '?')
            csv_url = r.get('url', '?')
            print(f"  {yr}年{mo}月: {csv_url[:80]}...")

        # 下載最新一個月的 CSV 並預覽前 3 筆
        if results:
            latest = results[-1]
            latest_url = latest.get('url', '')
            if latest_url:
                print(f"\n正在下載最新月份 CSV...")
                req2 = urllib.request.Request(latest_url, headers=headers)
                res2 = urllib.request.urlopen(req2, context=ctx, timeout=30)
                raw = res2.read()
                for enc in ('utf-8-sig', 'utf-8', 'big5', 'cp950'):
                    try:
                        text = raw.decode(enc)
                        break
                    except:
                        continue
                reader = csv.DictReader(io.StringIO(text))
                rows = list(reader)
                print(f"[成功] 共 {len(rows)} 筆 OD 記錄（站對站分時流量）")
                if rows:
                    print("欄位:", list(rows[0].keys()))
                    print("\n前 3 筆:")
                    for row in rows[:3]:
                        print(" ", row)

    except Exception as e:
        print("[失敗]", e)

if __name__ == '__main__':
    main()
