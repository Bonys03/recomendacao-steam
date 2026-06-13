from pathlib import Path

import numpy as np
import pandas as pd


FONTE = Path("steam_dataset.csv")
DIRETORIO_SAIDA = Path("steam_analysis")
DATA_ANALISE = pd.Timestamp("2026-06-12")
MIN_AVALIACOES_PARA_NOTA = 20
TAMANHO_MIN_GRUPO = 100

                                                                              
                                                                                
COLUNAS_DESLOCADAS = {
    "Name": "AppID",
    "Release date": "Name",
    "Estimated owners": "Release date",
    "Peak CCU": "Estimated owners",
    "Required age": "Peak CCU",
    "Price": "Required age",
    "Windows": "Windows",
    "Mac": "Mac",
    "Linux": "Linux",
    "Metacritic score": "Metacritic score",
    "Positive": "Positive",
    "Negative": "Negative",
    "Recommendations": "Recommendations",
    "Average playtime forever": "Average playtime forever",
    "Developers": "Developers",
    "Publishers": "Publishers",
    "Categories": "Categories",
    "Genres": "Genres",
    "Tags": "Tags",
}


def carregar_e_reparar() -> pd.DataFrame:
    colunas_brutas = list(dict.fromkeys(COLUNAS_DESLOCADAS.values()))
    bruto = pd.read_csv(FONTE, usecols=colunas_brutas, low_memory=False)
    return pd.DataFrame(
        {correto: bruto[deslocado] for correto, deslocado in COLUNAS_DESLOCADAS.items()}
    )


def numerico(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce")


def limpar_dataset(dados: pd.DataFrame) -> pd.DataFrame:
    dados = dados.copy()
    dados["release_date"] = pd.to_datetime(dados["Release date"], errors="coerce")

    partes_proprietarios = (
        dados["Estimated owners"]
        .astype("string")
        .str.replace(",", "", regex=False)
        .str.extract(r"^\s*(\d+)\s*-\s*(\d+)\s*$")
    )
    dados["owners_lower"] = numerico(partes_proprietarios[0])
    dados["owners_upper"] = numerico(partes_proprietarios[1])
    dados["owners_midpoint"] = (dados["owners_lower"] + dados["owners_upper"]) / 2

    for origem, destino in [
        ("Peak CCU", "peak_ccu"),
        ("Required age", "required_age"),
        ("Price", "price_usd"),
        ("Metacritic score", "metacritic_score"),
        ("Positive", "positive_reviews"),
        ("Negative", "negative_reviews"),
        ("Recommendations", "recommendations"),
        ("Average playtime forever", "avg_playtime_minutes"),
    ]:
        dados[destino] = numerico(dados[origem])

    dados["review_count"] = dados["positive_reviews"] + dados["negative_reviews"]
    dados["positive_ratio"] = np.where(
        dados["review_count"] > 0, dados["positive_reviews"] / dados["review_count"], np.nan
    )
    dados["platform_count"] = (
        dados[["Windows", "Mac", "Linux"]].fillna(False).astype(bool).sum(axis=1)
    )
    dados["price_band"] = pd.cut(
        dados["price_usd"],
        bins=[-0.01, 0, 5, 10, 20, 30, 60, np.inf],
        labels=["Free", "$0-5", "$5-10", "$10-20", "$20-30", "$30-60", "$60+"],
    ).astype("string")
    dados["release_year"] = dados["release_date"].dt.year

    texto_categorias = dados["Categories"].fillna("").astype(str)
    dados["play_mode"] = np.select(
        [
            texto_categorias.str.contains("Multi-player|Multiplayer", case=False),
            texto_categorias.str.contains("Single-player", case=False),
        ],
        ["Has multiplayer", "Single-player only"],
        default="Unspecified",
    )

    texto_nome = dados["Name"].fillna("").astype(str)
    texto_combinado = (
        texto_nome
        + ","
        + dados["Categories"].fillna("").astype(str)
        + ","
        + dados["Genres"].fillna("").astype(str)
        + ","
        + dados["Tags"].fillna("").astype(str)
    )
    excluido = texto_combinado.str.contains(
        r"\b(?:playtest|demo|soundtrack|server|benchmark|editor)\b",
        case=False,
        regex=True,
    )

    valido = (
        dados["release_date"].notna()
        & (dados["release_date"] <= DATA_ANALISE)
        & dados["owners_midpoint"].notna()
        & dados["Genres"].notna()
        & ~excluido
    )
    dados = dados.loc[valido].copy()
    dados = dados.drop_duplicates(
        subset=["Name", "release_date", "Developers"], keep="first"
    )

                                                                                   
    dados["commercial_game"] = (dados["price_usd"] > 0) & (dados["price_usd"] <= 100)
    comercial = dados["commercial_game"]
    limite_vendas = dados.loc[comercial, "owners_midpoint"].quantile(0.80)
    dados["high_sales"] = dados["owners_midpoint"] >= limite_vendas
    dados["well_rated"] = (
        (dados["review_count"] >= MIN_AVALIACOES_PARA_NOTA)
        & (dados["positive_ratio"] >= 0.75)
    )
    dados["success"] = dados["commercial_game"] & dados["high_sales"] & dados["well_rated"]
    dados.attrs["sales_threshold"] = float(limite_vendas)

    manter = [
        "Name",
        "release_date",
        "release_year",
        "Developers",
        "Publishers",
        "Categories",
        "Genres",
        "Tags",
        "price_usd",
        "price_band",
        "owners_lower",
        "owners_upper",
        "owners_midpoint",
        "peak_ccu",
        "positive_reviews",
        "negative_reviews",
        "review_count",
        "positive_ratio",
        "recommendations",
        "avg_playtime_minutes",
        "metacritic_score",
        "Windows",
        "Mac",
        "Linux",
        "platform_count",
        "play_mode",
        "commercial_game",
        "high_sales",
        "well_rated",
        "success",
    ]
    limpo = dados[manter].copy()
    limpo.attrs.update(dados.attrs)
    return limpo


def intervalo_wilson(sucessos: pd.Series, total: pd.Series) -> tuple[pd.Series, pd.Series]:
    z = 1.96
    taxa = sucessos / total
    denominador = 1 + z**2 / total
    centro = (taxa + z**2 / (2 * total)) / denominador
    margem = (
        z
        * np.sqrt((taxa * (1 - taxa) + z**2 / (4 * total)) / total)
        / denominador
    )
    return centro - margem, centro + margem


def resumir_grupos(
    quadro: pd.DataFrame, colunas_agrupamento: list[str], taxa_base: float
) -> pd.DataFrame:
    resultado = (
        quadro.groupby(colunas_agrupamento, observed=True)
        .agg(
            games=("success", "size"),
            successes=("success", "sum"),
            success_rate=("success", "mean"),
            median_owners=("owners_midpoint", "median"),
            median_price=("price_usd", "median"),
            median_positive_ratio=("positive_ratio", "median"),
            median_reviews=("review_count", "median"),
        )
        .reset_index()
    )
    resultado["lift_vs_baseline"] = resultado["success_rate"] / taxa_base
    resultado["ci_low"], resultado["ci_high"] = intervalo_wilson(
        resultado["successes"], resultado["games"]
    )
    resultado["evidence_score"] = resultado["ci_low"] * np.log1p(resultado["games"])
    return resultado.sort_values(
        ["evidence_score", "success_rate", "games"], ascending=False
    )


def resumo_expandido(
    quadro: pd.DataFrame, coluna_origem: str, nome_item: str, taxa_base: float
) -> pd.DataFrame:
    expandido = quadro.assign(
        **{
            nome_item: quadro[coluna_origem]
            .fillna("")
            .str.split(",")
            .map(lambda valores: [valor.strip() for valor in valores if valor.strip()])
        }
    ).explode(nome_item)
    expandido = expandido[expandido[nome_item].notna() & expandido[nome_item].ne("")]
    return resumir_grupos(expandido, [nome_item], taxa_base)


def correlacoes(quadro: pd.DataFrame) -> pd.DataFrame:
    valores = quadro[
        [
            "owners_midpoint",
            "price_usd",
            "peak_ccu",
            "review_count",
            "positive_ratio",
            "recommendations",
            "avg_playtime_minutes",
            "metacritic_score",
            "platform_count",
        ]
    ].copy()
    for coluna in [
        "owners_midpoint",
        "peak_ccu",
        "review_count",
        "recommendations",
        "avg_playtime_minutes",
    ]:
        valores[coluna] = np.log1p(valores[coluna].clip(lower=0))
    correlacao = valores.corr(method="spearman", min_periods=100)["owners_midpoint"]
    return correlacao.rename("spearman_correlation_with_log_owners").sort_values(
        ascending=False
    ).reset_index(name="spearman_correlation_with_log_owners").rename(
        columns={"index": "metric"}
    )


def principal() -> None:
    DIRETORIO_SAIDA.mkdir(exist_ok=True)
    reparado = carregar_e_reparar()
    limpo = limpar_dataset(reparado)
    comercial = limpo[limpo["commercial_game"]].copy()
    taxa_base = comercial["success"].mean()

    generos = resumo_expandido(comercial, "Genres", "Genre", taxa_base)
    tags = resumo_expandido(comercial, "Tags", "Tag", taxa_base)
    categorias = resumo_expandido(comercial, "Categories", "Category", taxa_base)
    faixas_preco = resumir_grupos(comercial, ["price_band"], taxa_base)
    modos_jogo = resumir_grupos(comercial, ["play_mode"], taxa_base)
    plataformas = resumir_grupos(comercial, ["platform_count"], taxa_base)
    anos_lancamento = resumir_grupos(comercial, ["release_year"], taxa_base)

    linhas_genero = comercial.assign(
        Genre=comercial["Genres"]
        .fillna("")
        .str.split(",")
        .map(lambda valores: [valor.strip() for valor in valores if valor.strip()])
    ).explode("Genre")
    combinacoes = resumir_grupos(
        linhas_genero[linhas_genero["Genre"].ne("")],
        ["Genre", "price_band", "play_mode", "platform_count"],
        taxa_base,
    )
    combinacoes = combinacoes[combinacoes["games"] >= TAMANHO_MIN_GRUPO].copy()

    tabelas = {
        "genres": generos[generos["games"] >= TAMANHO_MIN_GRUPO],
        "tags": tags[tags["games"] >= TAMANHO_MIN_GRUPO],
        "categories": categorias[categorias["games"] >= TAMANHO_MIN_GRUPO],
        "price_bands": faixas_preco,
        "play_modes": modos_jogo,
        "platforms": plataformas,
        "release_years": anos_lancamento,
        "combinations": combinacoes,
        "correlations": correlacoes(comercial),
    }

    limpo.to_csv(DIRETORIO_SAIDA / "steam_cleaned.csv", index=False)
    for nome, tabela in tabelas.items():
        tabela.to_csv(DIRETORIO_SAIDA / f"{nome}.csv", index=False)

    print(f"Jogos limpos: {len(limpo):,}")
    print(f"Jogos comerciais pagos: {len(comercial):,}")
    print(f"Arquivos gerados em: {DIRETORIO_SAIDA.resolve()}")


if __name__ == "__main__":
    principal()
