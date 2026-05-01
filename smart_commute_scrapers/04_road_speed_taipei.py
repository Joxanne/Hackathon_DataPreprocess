"""
04_road_speed_taipei.py - 台北市即時道路速率（VD 偵測器）
資料來源: tcgbusfs.blob.core.windows.net（台北市交通局，1分鐘更新）
格式: XML.gz 壓縮，直接下載解壓解析，無需 API Key
"""
import urllib.request, ssl, gzip, xml.etree.ElementTree as ET

def main():
    print("=== [04_road_speed_taipei.py] 台北市即時道路速率 (VD 偵測器) ===")
    url = "https://tcgbusfs.blob.core.windows.net/blobtisv/GetVD.xml.gz"
    ctx = ssl._create_unverified_context()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        raw = res.read()
        xml_text = gzip.decompress(raw).decode('utf-8', errors='replace')

        ns = {'vd': 'http://www.iii.org.tw/dax/vd'}
        root = ET.fromstring(xml_text)

        center = root.find('vd:CenterName', ns)
        exch_time = root.find('vd:ExchangeTime', ns)
        sections = root.findall('.//vd:SectionData', ns)

        print(f"[成功] 資料中心: {center.text if center is not None else '?'}")
        print(f"  更新時間: {exch_time.text if exch_time is not None else '?'}")
        print(f"  共 {len(sections)} 個路段偵測器")

        print("\n--- 前 5 個路段即時速率 ---")
        for sec in sections[:5]:
            sid   = sec.findtext('vd:SectionId', '?', ns)
            name  = sec.findtext('vd:SectionName', '?', ns)
            speed = sec.findtext('vd:AvgSpd', '?', ns)
            vol   = sec.findtext('vd:TotalVol', '?', ns)
            moe   = sec.findtext('vd:MOELevel', '?', ns)
            try:
                speed_f = float(speed)
                if speed_f > 60:
                    level = "暢通"
                elif speed_f > 30:
                    level = "輕壅塞"
                else:
                    level = "壅塞"
            except:
                level = "?"
            print(f"  [{sid}] {name}: 速率={speed} km/h ({level}), 流量={vol}, MOE={moe}")

    except Exception as e:
        print("[失敗]", e)

if __name__ == '__main__':
    main()
