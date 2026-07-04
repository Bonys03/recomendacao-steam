from __future__ import annotations

import argparse
import base64
import json
import os
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DB_PATH = Path("steam_database.sqlite")
TEMPLATE_PATH = Path("steam_elastic_template.json")
DEFAULT_ES_URL = "http://localhost:9200"
DEFAULT_INDEX = "steam_games"


def auth_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("ELASTIC_API_KEY")
    username = os.getenv("ELASTIC_USER")
    password = os.getenv("ELASTIC_PASSWORD")

    if api_key:
        headers["Authorization"] = f"ApiKey {api_key}"
    elif username and password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"

    return headers


def request(
    method: str,
    url: str,
    body: bytes | None = None,
    content_type: str = "application/json",
) -> tuple[int, str]:
    headers = auth_headers()
    headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        text = error.read().decode("utf-8", errors="replace")
        return error.code, text
    except urllib.error.URLError as error:
        raise ConnectionError(
            f"Nao foi possivel conectar ao Elasticsearch em {url}. "
            "Confirme se ele esta rodando."
        ) from error


def split_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item for item in value.split("||") if item]


def price_band(price: float | None) -> str | None:
    if price is None:
        return None
    if price == 0:
        return "Free"
    if price <= 5:
        return "$0-5"
    if price <= 10:
        return "$5-10"
    if price <= 20:
        return "$10-20"
    if price <= 30:
        return "$20-30"
    if price <= 60:
        return "$30-60"
    return "$60+"


def row_to_document(row: sqlite3.Row) -> dict[str, Any]:
    review_count = (row["positive_reviews"] or 0) + (row["negative_reviews"] or 0)
    owners_midpoint = None
    if row["owners_lower"] is not None and row["owners_upper"] is not None:
        owners_midpoint = (row["owners_lower"] + row["owners_upper"]) / 2

    positive_ratio = None
    if review_count > 0:
        positive_ratio = (row["positive_reviews"] or 0) / review_count

    release_year = None
    if row["release_date"]:
        release_year = int(row["release_date"][:4])

    return {
        "game_id": row["game_id"],
        "name": row["name"],
        "release_date": row["release_date"],
        "release_year": release_year,
        "price_usd": row["price_usd"],
        "price_band": price_band(row["price_usd"]),
        "owners_lower": row["owners_lower"],
        "owners_upper": row["owners_upper"],
        "owners_midpoint": owners_midpoint,
        "peak_ccu": row["peak_ccu"],
        "positive_reviews": row["positive_reviews"],
        "negative_reviews": row["negative_reviews"],
        "review_count": review_count,
        "positive_ratio": positive_ratio,
        "recommendations": row["recommendations"],
        "avg_playtime_minutes": row["avg_playtime_minutes"],
        "metacritic_score": row["metacritic_score"],
        "developers": split_list(row["developers"]),
        "publishers": split_list(row["publishers"]),
        "genres": split_list(row["genres"]),
        "categories": split_list(row["categories"]),
        "tags": split_list(row["tags"]),
        "platforms": split_list(row["platforms"]),
    }


def fetch_games(conn: sqlite3.Connection, batch_size: int, offset: int) -> list[dict[str, Any]]:
    sql = """
        SELECT
            g.game_id,
            g.name,
            g.release_date,
            g.price_usd,
            g.owners_lower,
            g.owners_upper,
            g.peak_ccu,
            g.positive_reviews,
            g.negative_reviews,
            g.recommendations,
            g.avg_playtime_minutes,
            g.metacritic_score,
            (
                SELECT group_concat(d.name, '||')
                FROM game_developers gd
                JOIN developers d ON d.developer_id = gd.developer_id
                WHERE gd.game_id = g.game_id
            ) AS developers,
            (
                SELECT group_concat(p.name, '||')
                FROM game_publishers gp
                JOIN publishers p ON p.publisher_id = gp.publisher_id
                WHERE gp.game_id = g.game_id
            ) AS publishers,
            (
                SELECT group_concat(ge.name, '||')
                FROM game_genres gg
                JOIN genres ge ON ge.genre_id = gg.genre_id
                WHERE gg.game_id = g.game_id
            ) AS genres,
            (
                SELECT group_concat(c.name, '||')
                FROM game_categories gc
                JOIN categories c ON c.category_id = gc.category_id
                WHERE gc.game_id = g.game_id
            ) AS categories,
            (
                SELECT group_concat(t.name, '||')
                FROM game_tags gt
                JOIN tags t ON t.tag_id = gt.tag_id
                WHERE gt.game_id = g.game_id
            ) AS tags,
            (
                SELECT group_concat(pl.name, '||')
                FROM game_platforms gpl
                JOIN platforms pl ON pl.platform_id = gpl.platform_id
                WHERE gpl.game_id = g.game_id
            ) AS platforms
        FROM games g
        ORDER BY g.game_id
        LIMIT ? OFFSET ?
    """
    rows = conn.execute(sql, (batch_size, offset)).fetchall()
    return [row_to_document(row) for row in rows]


def create_index(es_url: str, index_name: str, recreate: bool) -> None:
    if recreate:
        request("DELETE", f"{es_url}/{index_name}")

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template Elasticsearch nao encontrado: {TEMPLATE_PATH}")

    template_config = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    status, text = request(
        "PUT",
        f"{es_url}/_index_template/steam_games_template",
        json.dumps(template_config).encode("utf-8"),
    )
    if status not in {200, 201}:
        raise RuntimeError(f"Falha ao criar template Elasticsearch: HTTP {status} - {text}")

    status, text = request(
        "PUT",
        f"{es_url}/{index_name}",
    )
    if status not in {200, 201}:
        if status == 400 and "resource_already_exists_exception" in text:
            return
        raise RuntimeError(f"Falha ao criar indice {index_name}: HTTP {status} - {text}")


def bulk_index(es_url: str, index_name: str, docs: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    for doc in docs:
        lines.append(json.dumps({"index": {"_index": index_name, "_id": doc["game_id"]}}, ensure_ascii=False))
        lines.append(json.dumps(doc, ensure_ascii=False))

    body = ("\n".join(lines) + "\n").encode("utf-8")
    status, text = request(
        "POST",
        f"{es_url}/_bulk",
        body,
        content_type="application/x-ndjson",
    )
    if status not in {200, 201}:
        raise RuntimeError(f"Falha no bulk: HTTP {status} - {text}")

    result = json.loads(text)
    if result.get("errors"):
        first_error = next(
            item["index"].get("error")
            for item in result["items"]
            if item.get("index", {}).get("error")
        )
        raise RuntimeError(f"Bulk indexou com erros. Primeiro erro: {first_error}")


def load_elasticsearch(es_url: str, index_name: str, batch_size: int, limit: int | None, recreate: bool) -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Banco SQLite nao encontrado: {DB_PATH}")

    request("GET", es_url)
    create_index(es_url, index_name, recreate)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    if limit is not None:
        total = min(total, limit)

    indexed = 0
    while indexed < total:
        current_batch = min(batch_size, total - indexed)
        docs = fetch_games(conn, current_batch, indexed)
        if not docs:
            break
        bulk_index(es_url, index_name, docs)
        indexed += len(docs)
        print(f"Indexados: {indexed}/{total}")

    conn.close()
    request("POST", f"{es_url}/{index_name}/_refresh")
    print(f"Indice criado: {index_name}")
    print(f"Documentos indexados: {indexed}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cria um indice Elasticsearch com dados do Steam.")
    parser.add_argument("--es-url", default=os.getenv("ELASTIC_URL", DEFAULT_ES_URL))
    parser.add_argument("--index", default=DEFAULT_INDEX)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-recreate", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    load_elasticsearch(
        es_url=args.es_url.rstrip("/"),
        index_name=args.index,
        batch_size=args.batch_size,
        limit=args.limit,
        recreate=not args.no_recreate,
    )
