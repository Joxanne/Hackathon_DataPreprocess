"""
origin_bike_network.py - 大臺北自行車道路網
資料來源: PostgreSQL Dashboard DB

"""

import argparse
import uuid

import psycopg2
import psycopg2.extras
from psycopg2 import sql
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from config import EMBED_MODEL, PG_DASHBOARD, QDRANT, VECTOR_SIZE

# ── 資料集設定 ─────────────────────────────────────────────────────────────────
QDRANT_COLLECTION = "bike_network_tpe"

SOURCE_TABLES = {
    "taipei":    "bike_network_tpe",
    "newtaipei": "bike_network_new_tpe",
}


# ── Step 1: 從 PostgreSQL 讀取 ─────────────────────────────────────────────────
def load_from_db(city: str) -> list[dict]:
    """city: 'taipei' | 'newtaipei' | 'all'"""
    if city == "all":
        targets = list(SOURCE_TABLES.items())
    else:
        targets = [(city, SOURCE_TABLES[city])]

    conn = psycopg2.connect(**PG_DASHBOARD)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    rows = []
    for city_key, table in targets:
        cur.execute(
            sql.SQL("""
                SELECT ogc_fid, route_name, city_code, city, town,
                       road_section_start, road_section_end,
                       direction, cycling_length
                FROM public.{}
            """).format(sql.Identifier(table))
        )
        fetched = cur.fetchall()
        print(f"[DB] {table}：讀取 {len(fetched)} 筆")
        for r in fetched:
            rows.append({"_city_key": city_key, **dict(r)})

    cur.close()
    conn.close()
    print(f"[DB] 合計讀取 {len(rows)} 筆")
    return rows


# ── Step 2: 預處理 ─────────────────────────────────────────────────────────────
def preprocess(rows: list[dict]) -> list[dict]:
    print("[預處理] 正規化欄位 ...")
    records, skipped = [], 0

    for r in rows:
        route_name = (r.get("route_name") or "").strip()
        if not route_name:
            skipped += 1
            continue

        city      = (r.get("city")               or "").strip()
        town      = (r.get("town")               or "").strip()
        start     = (r.get("road_section_start") or "").strip()
        end       = (r.get("road_section_end")   or "").strip()
        direction = (r.get("direction")          or "").strip()
        length    = r.get("cycling_length")

        records.append({
            "ogc_fid":    r["ogc_fid"],
            "city_code":  (r.get("city_code") or "").strip(),
            "city_key":   r["_city_key"],
            "route_name": route_name,
            "city":       city,
            "town":       town,
            "start":      start,
            "end":        end,
            "direction":  direction,
            "length_m":   float(length) if length is not None else None,
        })

    print(f"[預處理] 有效 {len(records)} 筆，過濾 {skipped} 筆")
    return records


# ── Step 3: 向量化並寫入 Qdrant ────────────────────────────────────────────────
def save_to_qdrant(records: list[dict]) -> None:
    print("[Qdrant] 載入 embedding 模型 ...")
    model = SentenceTransformer(EMBED_MODEL)

    def _build_text(r: dict) -> str:
        parts = [f"passage: 自行車道：{r['route_name']}，位於{r['city']}"]
        if r["town"]:
            parts.append(r["town"])
        if r["start"] and r["end"]:
            parts.append(f"，路段{r['start']}至{r['end']}")
        elif r["start"]:
            parts.append(f"，起點{r['start']}")
        if r["direction"]:
            parts.append(f"，{r['direction']}")
        if r["length_m"] is not None:
            km = r["length_m"] / 1000
            parts.append(f"，全長{km:.2f}公里")
        return "".join(parts)

    texts = [_build_text(r) for r in records]
    print(f"[Qdrant] 生成 {len(texts)} 筆向量嵌入 ...")
    vectors = model.encode(
        texts, batch_size=64, normalize_embeddings=True, show_progress_bar=True
    )

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

    # Point ID = UUID v5(city_code + ogc_fid)，確保 deterministic 且跨表不衝突
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{r['city_code']}_{r['ogc_fid']}")),
            vector=v.tolist(),
            payload={
                "ogc_fid":    r["ogc_fid"],
                "city_code":  r["city_code"],
                "route_name": r["route_name"],
                "city":       r["city"],
                "town":       r["town"],
                "start":      r["start"],
                "end":        r["end"],
                "direction":  r["direction"],
                "length_m":   r["length_m"],
                "type":       "bike_network",
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
    parser = argparse.ArgumentParser(description="自行車道路網向量化管線")
    parser.add_argument(
        "--city",
        choices=["all", "taipei", "newtaipei"],
        default="all",
        help="all=雙北全部, taipei=臺北市, newtaipei=新北市",
    )
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"  Bike Network Pipeline  |  city={args.city}")
    print(f"{'='*50}\n")

    rows    = load_from_db(args.city)
    records = preprocess(rows)
    if not records:
        print("[警告] 無有效資料，結束。")
        raise SystemExit(0)
    save_to_qdrant(records)

    print(f"\n{'='*50}")
    print("  完成！")
    print(f"{'='*50}\n")
