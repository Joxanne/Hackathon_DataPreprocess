import urllib.request, ssl, json

def main():
    print("=== [04_pop_ntpc.py] 新北人口分布（區別） ===")
    # 新北市各區人數統計表 - 更新後的 Dataset OID
    url = "https://data.ntpc.gov.tw/api/datasets/292443d2-faef-452c-96cd-33053e7369b6/json?page=0&size=5"
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        res = urllib.request.urlopen(req, context=ctx, timeout=15).read()
        data = json.loads(res.decode('utf-8'))
        print("[成功] 新北市各區人口:")
        # 資料直接是 list，每筆包含 district, village, neighborhood, home, male, female, total
        if isinstance(data, list):
            for row in data[:5]:
                district = row.get('district', '?')
                total = row.get('total', '?')
                male = row.get('male', '?')
                female = row.get('female', '?')
                print(f"  {district}: 總人口={total}, 男={male}, 女={female}")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print("[失敗]", e)

if __name__ == '__main__':
    main()
