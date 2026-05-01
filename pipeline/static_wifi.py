"""
static_wifi.py - TaipeiFree WiFi 熱點資料
"""
import argparse
import csv
import io
import ssl
import urllib.request
import uuid

import psycopg2
from psycopg2.extras import execute_batch
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

from config import PG_DASHBOARD, QDRANT, EMBED_MODEL, VECTOR_SIZE

# ── 資料集設定 ─────────────────────────────────────────────────────────────────
QDRANT_COLLECTION = "wifi_hotspot_tpe"

WIFI_URL = (
    "https://data.taipei/api/frontstage/tpeod/dataset/resource.download"
    "?rid=549b3a9b-eb6c-4cb1-848b-8c238735e2db"
)


# ── Step 1: 爬蟲 ──────────────────────────────────────────────────────────────
def crawl() -> list[dict]:
    print("[爬蟲] 下載 TaipeiFree WiFi CSV ...")
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(WIFI_URL, headers={"User-Agent": "Mozilla/5.0"})
    res = urllib.request.urlopen(req, context=ctx, timeout=20)
    raw = res.read()

    text = None
    for enc in ("utf-8-sig", "utf-8", "big5", "cp950"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError("無法解碼 CSV 檔案")

    rows = list(csv.DictReader(io.StringIO(text)))
    print(f"[爬蟲] 取得 {len(rows)} 筆原始資料")
    return rows


def load_sample(path: str) -> list[dict]:
    print(f"[Sample] 讀取本地檔案：{path}")
    for enc in ("utf-8-sig", "utf-8", "big5", "cp950"):
        try:
            with open(path, encoding=enc, newline="") as f:
                rows = list(csv.DictReader(f))
            print(f"[Sample] 讀取 {len(rows)} 筆")
            return rows
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"無法讀取 {path}")


# ── Step 2: 預處理 ─────────────────────────────────────────────────────────────
def preprocess(rows: list[dict]) -> list[dict]:
    print("[預處理] 清洗與正規化 ...")
    records, skipped = [], 0
    for r in rows:
        try:
            lat = float(r.get("LATITUDE") or 0)
            lon = float(r.get("LONGITUDE") or 0)
        except (ValueError, TypeError):
            skipped += 1
            continue

        # 過濾非台北大都會範圍的座標
        if not (24.9 <= lat <= 25.35 and 121.3 <= lon <= 121.75):
            skipped += 1
            continue

        site_id = (r.get("SITE_ID") or "").strip()
        name    = (r.get("NAME")    or r.get("E_NAME") or "").strip()
        area    = (r.get("AREA")    or "").strip()
        address = (r.get("ADDR")    or r.get("E_ADDR") or "").strip()

        if not site_id or not name:
            skipped += 1
            continue

        records.append({
            "site_id":   site_id,
            "name":      name,
            "area":      area,
            "address":   address,
            "latitude":  lat,
            "longitude": lon,
        })

    print(f"[預處理] 有效 {len(records)} 筆，過濾 {skipped} 筆")
    return records


# ── Step 3: 寫入 PostgreSQL ────────────────────────────────────────────────────
def save_to_postgres(records: list[dict]) -> None:
    print("[PostgreSQL] 連線中 ...")
    conn = psycopg2.connect(**PG_DASHBOARD)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.wifi_hotspot_tpe (
            ogc_fid    SERIAL PRIMARY KEY,
            data_time  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            site_id    VARCHAR(50) UNIQUE NOT NULL,
            name       TEXT        NOT NULL,
            area       VARCHAR(50),
            address    TEXT,
            latitude   DOUBLE PRECISION,
            longitude  DOUBLE PRECISION,
            _ctime     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            _mtime     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """)

    execute_batch(cur, """
        INSERT INTO public.wifi_hotspot_tpe
            (site_id, name, area, address, latitude, longitude, data_time, _mtime)
        VALUES
            (%(site_id)s, %(name)s, %(area)s, %(address)s,
             %(latitude)s, %(longitude)s,
             CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (site_id) DO UPDATE SET
            name      = EXCLUDED.name,
            area      = EXCLUDED.area,
            address   = EXCLUDED.address,
            latitude  = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            data_time = EXCLUDED.data_time,
            _mtime    = EXCLUDED._mtime
    """, records, page_size=500)

    conn.commit()
    cur.close()
    conn.close()
    print(f"[PostgreSQL] 寫入完成（{len(records)} 筆）")


# ── Step 4: 向量化並寫入 Qdrant ────────────────────────────────────────────────
def save_to_qdrant(records: list[dict]) -> None:
    print("[Qdrant] 載入 embedding 模型 ...")
    model = SentenceTransformer(EMBED_MODEL)

    # e5 模型文件端用 "passage: " 前綴效果最佳
    texts = [
        f"passage: WiFi熱點：{r['name']}，位於{r['area']}{r['address']}"
        for r in records
    ]
    print(f"[Qdrant] 生成 {len(texts)} 筆向量嵌入 ...")
    vectors = model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=True)

    client = QdrantClient(**QDRANT)

    existing = {c.name for c in client.get_collections().collections}
    if QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"[Qdrant] 建立 collection：{QDRANT_COLLECTION}")
    else:
        print(f"[Qdrant] collection 已存在，執行 upsert")

    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, r["site_id"])),
            vector=v.tolist(),
            payload={
                "site_id":   r["site_id"],
                "name":      r["name"],
                "area":      r["area"],
                "address":   r["address"],
                "latitude":  r["latitude"],
                "longitude": r["longitude"],
                "type":      "wifi_hotspot",
            },
        )
        for r, v in zip(records, vectors)
    ]
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=QDRANT_COLLECTION, points=batch)
        print(f"[Qdrant] 上傳 {min(i + batch_size, len(points))}/{len(points)} ...")
    print(f"[Qdrant] 上傳完成（{len(points)} 筆）")


# ── 主程式 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TaipeiFree WiFi 資料管線")
    parser.add_argument(
        "--mode",
        choices=["periodic", "ondemand", "sample"],
        default="ondemand",
        help="periodic=定期排程, ondemand=AI觸發, sample=本地CSV",
    )
    parser.add_argument(
        "--sample-path",
        default="",
        help="sample 模式下的 CSV 路徑",
    )
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"  WiFi Pipeline  |  mode={args.mode}")
    print(f"{'='*50}\n")

    if args.mode in ("periodic", "ondemand"):
        rows = crawl()
    else:
        if not args.sample_path:
            print("[錯誤] sample 模式需提供 --sample-path")
            raise SystemExit(1)
        rows = load_sample(args.sample_path)

    records = preprocess(rows)
    if not records:
        print("[警告] 無有效資料，結束。")
        raise SystemExit(0)
    save_to_postgres(records)
    save_to_qdrant(records)

    print(f"\n{'='*50}")
    print("  完成！")
    print(f"{'='*50}\n")
