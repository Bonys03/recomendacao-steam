from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


CSV_LIMPO = Path("steam_analysis/steam_cleaned.csv")
BANCO_SAIDA = Path("steam_database.sqlite")
SCHEMA_SAIDA = Path("steam_schema.sql")

COLUNAS_GAMES = [
    "game_id",
    "name",
    "release_date",
    "price_usd",
    "owners_lower",
    "owners_upper",
    "peak_ccu",
    "positive_reviews",
    "negative_reviews",
    "recommendations",
    "avg_playtime_minutes",
    "metacritic_score",
]

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS game_tags;
DROP TABLE IF EXISTS game_genres;
DROP TABLE IF EXISTS game_categories;
DROP TABLE IF EXISTS game_platforms;
DROP TABLE IF EXISTS game_developers;
DROP TABLE IF EXISTS game_publishers;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS platforms;
DROP TABLE IF EXISTS developers;
DROP TABLE IF EXISTS publishers;
DROP TABLE IF EXISTS games;

CREATE TABLE games (
    game_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    release_date TEXT,
    price_usd REAL,
    owners_lower INTEGER,
    owners_upper INTEGER,
    peak_ccu INTEGER,
    positive_reviews INTEGER,
    negative_reviews INTEGER,
    recommendations INTEGER,
    avg_playtime_minutes INTEGER,
    metacritic_score INTEGER
);

CREATE TABLE developers (
    developer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE publishers (
    publisher_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE genres (
    genre_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE tags (
    tag_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE platforms (
    platform_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE game_developers (
    game_id INTEGER NOT NULL,
    developer_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, developer_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (developer_id) REFERENCES developers(developer_id) ON DELETE CASCADE
);

CREATE TABLE game_publishers (
    game_id INTEGER NOT NULL,
    publisher_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, publisher_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id) ON DELETE CASCADE
);

CREATE TABLE game_genres (
    game_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, genre_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
);

CREATE TABLE game_categories (
    game_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, category_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);

CREATE TABLE game_tags (
    game_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, tag_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
);

CREATE TABLE game_platforms (
    game_id INTEGER NOT NULL,
    platform_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, platform_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id) ON DELETE CASCADE
);

CREATE INDEX idx_games_name ON games(name);
CREATE INDEX idx_games_release_date ON games(release_date);
CREATE INDEX idx_game_developers_developer ON game_developers(developer_id);
CREATE INDEX idx_game_publishers_publisher ON game_publishers(publisher_id);
CREATE INDEX idx_game_genres_genre ON game_genres(genre_id);
CREATE INDEX idx_game_categories_category ON game_categories(category_id);
CREATE INDEX idx_game_tags_tag ON game_tags(tag_id);
CREATE INDEX idx_game_platforms_platform ON game_platforms(platform_id);

"""


def vazio_para_none(valor: str) -> str | None:
    valor = (valor or "").strip()
    return valor if valor else None


def inteiro(valor: str) -> int | None:
    valor = vazio_para_none(valor)
    return int(float(valor)) if valor is not None else None


def real(valor: str) -> float | None:
    valor = vazio_para_none(valor)
    return float(valor) if valor is not None else None


def booleano(valor: str) -> bool:
    return str(valor).strip().lower() == "true"


def itens(texto: str) -> list[str]:
    vistos: set[str] = set()
    resultado: list[str] = []
    for item in (texto or "").split(","):
        nome = item.strip()
        if nome and nome.casefold() not in vistos:
            vistos.add(nome.casefold())
            resultado.append(nome)
    return resultado


def id_por_nome(
    conexao: sqlite3.Connection,
    tabela: str,
    coluna_id: str,
    nome: str,
    cache: dict[str, int],
) -> int:
    chave = nome.casefold()
    if chave in cache:
        return cache[chave]

    conexao.execute(f"INSERT OR IGNORE INTO {tabela} (name) VALUES (?)", (nome,))
    row = conexao.execute(
        f"SELECT {coluna_id} FROM {tabela} WHERE name = ?",
        (nome,),
    ).fetchone()
    cache[chave] = int(row[0])
    return cache[chave]


def inserir_relacoes(
    conexao: sqlite3.Connection,
    game_id: int,
    nomes: list[str],
    tabela_item: str,
    coluna_id: str,
    tabela_relacao: str,
    cache: dict[str, int],
) -> None:
    for nome in nomes:
        item_id = id_por_nome(conexao, tabela_item, coluna_id, nome, cache)
        conexao.execute(
            f"INSERT OR IGNORE INTO {tabela_relacao} (game_id, {coluna_id}) VALUES (?, ?)",
            (game_id, item_id),
        )


def criar_banco() -> None:
    if not CSV_LIMPO.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {CSV_LIMPO}")

    if BANCO_SAIDA.exists():
        BANCO_SAIDA.unlink()

    SCHEMA_SAIDA.write_text(SCHEMA_SQL.strip() + "\n", encoding="utf-8")

    conexao = sqlite3.connect(BANCO_SAIDA)
    conexao.executescript(SCHEMA_SQL)

    caches = {
        "developers": {},
        "publishers": {},
        "genres": {},
        "categories": {},
        "tags": {},
        "platforms": {},
    }

    with CSV_LIMPO.open("r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for game_id, linha in enumerate(leitor, start=1):
            valores_game = {
                "game_id": game_id,
                "name": linha["Name"],
                "release_date": vazio_para_none(linha["release_date"]),
                "price_usd": real(linha["price_usd"]),
                "owners_lower": inteiro(linha["owners_lower"]),
                "owners_upper": inteiro(linha["owners_upper"]),
                "peak_ccu": inteiro(linha["peak_ccu"]),
                "positive_reviews": inteiro(linha["positive_reviews"]),
                "negative_reviews": inteiro(linha["negative_reviews"]),
                "recommendations": inteiro(linha["recommendations"]),
                "avg_playtime_minutes": inteiro(linha["avg_playtime_minutes"]),
                "metacritic_score": inteiro(linha["metacritic_score"]),
            }

            placeholders = ", ".join("?" for _ in COLUNAS_GAMES)
            conexao.execute(
                f"INSERT INTO games ({', '.join(COLUNAS_GAMES)}) VALUES ({placeholders})",
                [valores_game[coluna] for coluna in COLUNAS_GAMES],
            )

            inserir_relacoes(
                conexao,
                game_id,
                itens(linha["Developers"]),
                "developers",
                "developer_id",
                "game_developers",
                caches["developers"],
            )
            inserir_relacoes(
                conexao,
                game_id,
                itens(linha["Publishers"]),
                "publishers",
                "publisher_id",
                "game_publishers",
                caches["publishers"],
            )
            inserir_relacoes(
                conexao,
                game_id,
                itens(linha["Genres"]),
                "genres",
                "genre_id",
                "game_genres",
                caches["genres"],
            )
            inserir_relacoes(
                conexao,
                game_id,
                itens(linha["Categories"]),
                "categories",
                "category_id",
                "game_categories",
                caches["categories"],
            )
            inserir_relacoes(
                conexao,
                game_id,
                itens(linha["Tags"]),
                "tags",
                "tag_id",
                "game_tags",
                caches["tags"],
            )

            plataformas = []
            if booleano(linha["Windows"]):
                plataformas.append("Windows")
            if booleano(linha["Mac"]):
                plataformas.append("Mac")
            if booleano(linha["Linux"]):
                plataformas.append("Linux")
            inserir_relacoes(
                conexao,
                game_id,
                plataformas,
                "platforms",
                "platform_id",
                "game_platforms",
                caches["platforms"],
            )

            if game_id % 5000 == 0:
                conexao.commit()

    conexao.commit()
    conexao.execute("VACUUM")
    conexao.close()


if __name__ == "__main__":
    criar_banco()
    print(f"Banco criado: {BANCO_SAIDA}")
    print(f"Schema SQL criado: {SCHEMA_SAIDA}")
