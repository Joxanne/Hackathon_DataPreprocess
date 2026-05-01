import urllib.request, ssl, json

# ============================================================
#  TDX 運輸資料流通服務 API
#  需申請帳號取得 Client ID & Client Secret：
#  https://tdx.transportdata.tw/
# ============================================================
TDX_CLIENT_ID     = "YOUR_CLIENT_ID"      # 請替換為申請到的 ID
TDX_CLIENT_SECRET = "YOUR_CLIENT_SECRET"  # 請替換為申請到的 Secret
TDX_TOKEN_URL = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"

def get_tdx_token(ctx):
    """取得 TDX Access Token（有效期 86400 秒）"""
    body = (
        f"grant_type=client_credentials"
        f"&client_id={TDX_CLIENT_ID}"
        f"&client_secret={TDX_CLIENT_SECRET}"
    ).encode('utf-8')
    req = urllib.request.Request(
        TDX_TOKEN_URL,
        data=body,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST'
    )
    res = urllib.request.urlopen(req, context=ctx, timeout=15).read()
    token_data = json.loads(res.decode('utf-8'))
    return token_data.get('access_token')

def tdx_get(url, token, ctx):
    """使用 Token 呼叫 TDX API"""
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    })
    res = urllib.request.urlopen(req, context=ctx, timeout=20).read()
    return json.loads(res.decode('utf-8'))

def main():
    print("=== [03_tdx_metro.py] 台北捷運站別進出量 & 班次資訊 (TDX API) ===")
    ctx = ssl._create_unverified_context()

    if TDX_CLIENT_ID == "YOUR_CLIENT_ID":
        print("[跳過] 尚未設定 TDX_CLIENT_ID，請至 https://tdx.transportdata.tw/ 申請帳號")
        print("       申請完成後將 YOUR_CLIENT_ID 和 YOUR_CLIENT_SECRET 填入此檔案")
        print("\n--- TDX 可用端點說明 ---")
        print("  捷運即時列車位置:")
        print("    GET https://tdx.transportdata.tw/api/basic/v2/Rail/Metro/LiveBoard/TRTC?$top=5&$format=JSON")
        print("  捷運站別時間進出量:")
        print("    GET https://tdx.transportdata.tw/api/basic/v2/Rail/Metro/ODFare/TRTC?$top=5&$format=JSON")
        print("  公車即時動態 (台北):")
        print("    GET https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taipei/{路線名}?$format=JSON")
        print("  YouBike 站點即時 (新北, 需TDX):")
        print("    GET https://tdx.transportdata.tw/api/basic/v2/Bike/Availability/City/NewTaipei?$top=5&$format=JSON")
        return

    try:
        print("正在取得 TDX Token...")
        token = get_tdx_token(ctx)
        print("[成功] Token 取得完成")

        # --- 捷運即時列車位置 ---
        metro_url = "https://tdx.transportdata.tw/api/basic/v2/Rail/Metro/LiveBoard/TRTC?$top=5&$format=JSON"
        print("\n=== 捷運即時列車 ===")
        metro_data = tdx_get(metro_url, token, ctx)
        if isinstance(metro_data, list):
            for r in metro_data[:3]:
                print(json.dumps(r, ensure_ascii=False, indent=2))

        # --- 台北市公車即時 ETA (以 307 路為例) ---
        bus_url = "https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taipei/307?$top=5&$format=JSON"
        print("\n=== 公車 307 即時 ETA ===")
        bus_data = tdx_get(bus_url, token, ctx)
        if isinstance(bus_data, list):
            for r in bus_data[:3]:
                print(json.dumps(r, ensure_ascii=False, indent=2))

    except Exception as e:
        print("[失敗]", e)
        if "401" in str(e) or "403" in str(e):
            print("[提示] Token 無效或已過期，請確認 CLIENT_ID 和 CLIENT_SECRET 是否正確")

if __name__ == '__main__':
    main()
