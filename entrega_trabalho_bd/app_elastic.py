from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any

import pandas as pd
import streamlit as st

from steam_dashboard_core import montar_tabelas, preparar_limpo, renderizar_dashboard


DEFAULT_ES_URL = os.getenv("ELASTIC_URL", "http://localhost:9200")
DEFAULT_INDEX = os.getenv("ELASTIC_INDEX", "steam_games")


st.set_page_config(
    page_title="Steam Elasticsearch - Oportunidades",
    layout="wide",
)


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


def elastic_request(method: str, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=auth_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as error:
        text = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {text}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Nao foi possivel conectar ao Elasticsearch: {error.reason}") from error


@st.cache_data(show_spinner="Lendo documentos do Elasticsearch...")
def carregar_jogos_elastic(es_url: str, index_name: str, batch_size: int = 2000) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    search_after: list[Any] | None = None

    while True:
        body: dict[str, Any] = {
            "size": batch_size,
            "sort": [{"game_id": "asc"}],
            "query": {"match_all": {}},
            "_source": [
                "game_id",
                "name",
                "release_date",
                "release_year",
                "price_usd",
                "owners_lower",
                "owners_upper",
                "peak_ccu",
                "positive_reviews",
                "negative_reviews",
                "recommendations",
                "avg_playtime_minutes",
                "metacritic_score",
                "developers",
                "publishers",
                "genres",
                "categories",
                "tags",
                "platforms",
            ],
        }
        if search_after is not None:
            body["search_after"] = search_after

        response = elastic_request("POST", f"{es_url.rstrip('/')}/{index_name}/_search", body)
        hits = response.get("hits", {}).get("hits", [])
        if not hits:
            break

        for hit in hits:
            source = hit["_source"]
            rows.append(
                {
                    "game_id": source.get("game_id"),
                    "Name": source.get("name"),
                    "release_date": source.get("release_date"),
                    "release_year": source.get("release_year"),
                    "price_usd": source.get("price_usd"),
                    "owners_lower": source.get("owners_lower"),
                    "owners_upper": source.get("owners_upper"),
                    "peak_ccu": source.get("peak_ccu"),
                    "positive_reviews": source.get("positive_reviews"),
                    "negative_reviews": source.get("negative_reviews"),
                    "recommendations": source.get("recommendations"),
                    "avg_playtime_minutes": source.get("avg_playtime_minutes"),
                    "metacritic_score": source.get("metacritic_score"),
                    "Developers": ",".join(source.get("developers") or []),
                    "Publishers": ",".join(source.get("publishers") or []),
                    "Categories": ",".join(source.get("categories") or []),
                    "Genres": ",".join(source.get("genres") or []),
                    "Tags": ",".join(source.get("tags") or []),
                    "Platforms": ",".join(source.get("platforms") or []),
                }
            )
        search_after = hits[-1].get("sort")

    return pd.DataFrame(rows)


with st.sidebar:
    es_url = st.text_input("Elasticsearch URL", DEFAULT_ES_URL)
    index_name = st.text_input("Indice", DEFAULT_INDEX)

try:
    jogos = carregar_jogos_elastic(es_url, index_name)
    if jogos.empty:
        st.error("Indice vazio. Execute `python criar_banco_elasticsearch.py` antes.")
        st.stop()
    dados = montar_tabelas(preparar_limpo(jogos))
except Exception as error:
    st.error(str(error))
    st.code("python criar_banco_elasticsearch.py", language="powershell")
    st.stop()

renderizar_dashboard(dados, "Elasticsearch desnormalizado")
