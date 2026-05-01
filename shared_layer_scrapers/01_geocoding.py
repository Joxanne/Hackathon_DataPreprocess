import urllib.request, ssl, json
def main():
    print("=== [01_geocoding.py] 地理編碼（地址→座標） ===")
    url = "https://tgos.nat.gov.tw/TGOS_WEB_API/Web/Rest/TGOS_QueryAddr.aspx?"
    print("通常需要 API Key。此處僅示範介接邏輯：", url)
    print("資料元重點: [X: 121.5, Y: 25.0, Address: '...']")
if __name__ == '__main__':
    main()
