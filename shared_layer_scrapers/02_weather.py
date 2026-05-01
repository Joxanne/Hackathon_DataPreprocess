import urllib.request, ssl, json
def main():
    print("=== [02_weather.py] 即時氣象 / 颱風 / 地震 ===")
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWA-098BE5E3-2529-46C2-A82E-F996D8BA9D98&format=JSON"
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, context=ctx).read()
        data = json.loads(res.decode('utf-8'))
        records = data.get('records', {}).get('Station', [])[:2]
        print("[成功] 即時氣象資料樣本:")
        print(json.dumps(records, ensure_ascii=False, indent=2))
    except Exception as e:
        print("[失敗]", e)
if __name__ == '__main__':
    main()
