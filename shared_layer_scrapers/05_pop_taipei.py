import urllib.request, ssl, json

def main():
    print("=== [05_pop_taipei.py] 台北人口分布（區別） ===")
    # 臺北市各行政區最新月份人口數及戶數 - 更新後的 Dataset ID
    url = "https://data.taipei/api/v1/dataset/9681db4c-fb1b-4a23-9013-e74483b6b046?scope=resourceAquire&limit=5"
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        res = urllib.request.urlopen(req, context=ctx, timeout=15).read()
        data = json.loads(res.decode('utf-8'))
        # 回傳格式: {"result": {"limit":..., "offset":..., "count":..., "results": [...]}}
        result = data.get('result', {})
        rows = result.get('results', [])
        if not rows:
            print("[警告] 查無資料，請確認API端點。")
            return
        print("[成功] 台北市各區人口:")
        for row in rows:
            district = row.get('行政區', '?').strip()
            total = row.get('人口數_合計數量', '?')
            male = row.get('人口數_男數量', '?')
            female = row.get('人口數_女數量', '?')
            year = row.get('年份', '?')
            month = row.get('月份', '?')
            print(f"  [{year}/{month}] {district}: 總={total}, 男={male}, 女={female}")
    except Exception as e:
        print("[失敗]", e, "(若API變更可能需確認新URL)")

if __name__ == '__main__':
    main()
