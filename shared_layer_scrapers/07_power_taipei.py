import urllib.request, ssl
from bs4 import BeautifulSoup

def main():
    print("=== [07_power_taipei.py] 北市計畫停電通報 (台電官網爬蟲) ===")
    # 台電計畫性工作停電專區查詢頁
    url = "https://www.taipower.com.tw/2289/2406/2420/2421/simpleList"
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9',
        })
        res = urllib.request.urlopen(req, context=ctx, timeout=15).read().decode('utf-8')
        soup = BeautifulSoup(res, 'html.parser')

        # 嘗試找計畫停電查詢區塊
        content = soup.find('div', class_='content-box') or \
                  soup.find('div', id='content') or \
                  soup.find('main') or \
                  soup.find('article')

        print("[成功]")
        if content:
            text = content.get_text(separator='\n', strip=True)
            # 過濾空行
            lines = [l for l in text.split('\n') if l.strip()]
            print("--- 計畫停電專區說明 ---")
            for line in lines[:20]:
                print(f"  {line}")
        else:
            # 直接找含停電資訊的段落
            paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'li'])
            outage_lines = []
            for p in paragraphs:
                t = p.get_text(strip=True)
                if ('停電' in t or '供電' in t) and len(t) > 5:
                    outage_lines.append(t)

            if outage_lines:
                print("--- 停電相關內容 ---")
                for line in outage_lines[:15]:
                    print(f"  {line}")
            else:
                print("  無法解析頁面主要內容（可能為 JS 動態載入）")

        # 同時顯示停電查詢服務連結
        print("\n--- 台電停電相關服務連結 ---")
        links = soup.find_all('a', href=True)
        power_links = [(a.get_text(strip=True), a['href'])
                       for a in links
                       if '停電' in a.get_text() and len(a.get_text(strip=True)) > 2]
        seen = set()
        for text, href in power_links:
            if href not in seen:
                seen.add(href)
                full_url = href if href.startswith('http') else f"https://www.taipower.com.tw{href}"
                print(f"  [{text}] {full_url}")
                if len(seen) >= 5:
                    break

        if not seen:
            print("  停電查詢: https://service.taipower.com.tw/nds/")
            print("  計畫停電公告: https://www.taipower.com.tw/2289/2406/2420/2421/simpleList")

    except Exception as e:
        print("[失敗]", e)
        print("[備用連結] 請至 https://service.taipower.com.tw/nds/ 查詢停電資訊")

if __name__ == '__main__':
    main()
