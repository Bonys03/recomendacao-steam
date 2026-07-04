from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from steam_dashboard_core import montar_tabelas, preparar_limpo, renderizar_dashboard


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "steam_database.sqlite"


st.set_page_config(
    page_title="Steam SQL - Oportunidades",
    layout="wide",
)


@st.cache_data(show_spinner="Lendo dados do SQLite...")
def carregar_jogos_sql() -> pd.DataFrame:
    sql = """
        SELECT
            g.game_id,
            g.name AS Name,
            g.release_date,
            CAST(strftime('%Y', g.release_date) AS INTEGER) AS release_year,
            g.price_usd,
            g.owners_lower,
            g.owners_upper,
            g.peak_ccu,
            g.positive_reviews,
            g.negative_reviews,
            g.recommendations,
            g.avg_playtime_minutes,
            g.metacritic_score,
            COALESCE((
                SELECT group_concat(d.name, ',')
                FROM game_developers gd
                JOIN developers d ON d.developer_id = gd.developer_id
                WHERE gd.game_id = g.game_id
            ), '') AS Developers,
            COALESCE((
                SELECT group_concat(p.name, ',')
                FROM game_publishers gp
                JOIN publishers p ON p.publisher_id = gp.publisher_id
                WHERE gp.game_id = g.game_id
            ), '') AS Publishers,
            COALESCE((
                SELECT group_concat(c.name, ',')
                FROM game_categories gc
                JOIN categories c ON c.category_id = gc.category_id
                WHERE gc.game_id = g.game_id
            ), '') AS Categories,
            COALESCE((
                SELECT group_concat(ge.name, ',')
                FROM game_genres gg
                JOIN genres ge ON ge.genre_id = gg.genre_id
                WHERE gg.game_id = g.game_id
            ), '') AS Genres,
            COALESCE((
                SELECT group_concat(t.name, ',')
                FROM game_tags gt
                JOIN tags t ON t.tag_id = gt.tag_id
                WHERE gt.game_id = g.game_id
            ), '') AS Tags,
            COALESCE((
                SELECT group_concat(pl.name, ',')
                FROM game_platforms gpl
                JOIN platforms pl ON pl.platform_id = gpl.platform_id
                WHERE gpl.game_id = g.game_id
            ), '') AS Platforms
        FROM games g
        ORDER BY g.game_id
    """
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn)


if not DB_PATH.exists():
    st.error("Banco SQLite nao encontrado. Execute `python criar_banco_steam.py` antes.")
    st.stop()

try:
    dados = montar_tabelas(preparar_limpo(carregar_jogos_sql()))
except Exception as error:
    st.error(f"Falha ao carregar dados do SQLite: {error}")
    st.stop()

renderizar_dashboard(dados, "SQLite normalizado")
