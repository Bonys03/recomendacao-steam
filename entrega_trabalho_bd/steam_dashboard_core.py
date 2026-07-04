from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from steam_calculo import TAMANHO_MIN_GRUPO, correlacoes, resumir_grupos, resumo_expandido


DESTAQUE = "#2563eb"
SUCESSO = "#16a34a"
NEUTRO = "#94a3b8"
AVISO = "#d97706"

TRADUCAO_MODOS = {
    "Has multiplayer": "Possui multijogador",
    "Single-player only": "Somente um jogador",
    "Unspecified": "Nao especificado",
}

TRADUCAO_METRICAS = {
    "price usd": "Preco",
    "peak ccu": "Pico de jogadores simultaneos",
    "review count": "Quantidade de avaliacoes",
    "positive ratio": "Proporcao de avaliacoes positivas",
    "recommendations": "Recomendacoes",
    "avg playtime minutes": "Tempo medio de jogo",
    "metacritic score": "Nota Metacritic",
    "platform count": "Quantidade de plataformas",
}


def preparar_limpo(jogos: pd.DataFrame) -> pd.DataFrame:
    dados = jogos.copy()
    dados["release_date"] = pd.to_datetime(dados["release_date"], errors="coerce")
    dados["release_year"] = dados["release_date"].dt.year.fillna(dados["release_year"])

    for coluna in [
        "price_usd",
        "owners_lower",
        "owners_upper",
        "peak_ccu",
        "positive_reviews",
        "negative_reviews",
        "recommendations",
        "avg_playtime_minutes",
        "metacritic_score",
    ]:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce").fillna(0)

    dados["owners_midpoint"] = (dados["owners_lower"] + dados["owners_upper"]) / 2
    dados["review_count"] = dados["positive_reviews"] + dados["negative_reviews"]
    dados["positive_ratio"] = np.where(
        dados["review_count"] > 0,
        dados["positive_reviews"] / dados["review_count"],
        np.nan,
    )
    dados["price_band"] = pd.cut(
        dados["price_usd"],
        bins=[-0.01, 0, 5, 10, 20, 30, 60, np.inf],
        labels=["Free", "$0-5", "$5-10", "$10-20", "$20-30", "$30-60", "$60+"],
    ).astype("string")

    for plataforma in ["Windows", "Mac", "Linux"]:
        dados[plataforma] = dados["Platforms"].fillna("").str.contains(plataforma, case=False)
    dados["platform_count"] = dados[["Windows", "Mac", "Linux"]].astype(bool).sum(axis=1)

    texto_categorias = dados["Categories"].fillna("").astype(str)
    dados["play_mode"] = np.select(
        [
            texto_categorias.str.contains("Multi-player|Multiplayer", case=False, regex=True),
            texto_categorias.str.contains("Single-player", case=False, regex=False),
        ],
        ["Has multiplayer", "Single-player only"],
        default="Unspecified",
    )

    dados["commercial_game"] = (dados["price_usd"] > 0) & (dados["price_usd"] <= 100)
    limite_vendas = dados.loc[dados["commercial_game"], "owners_midpoint"].quantile(0.80)
    dados["high_sales"] = dados["owners_midpoint"] >= limite_vendas
    dados["well_rated"] = (dados["review_count"] >= 20) & (dados["positive_ratio"] >= 0.75)
    dados["success"] = dados["commercial_game"] & dados["high_sales"] & dados["well_rated"]

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
    return dados[manter].copy()


def montar_tabelas(limpo: pd.DataFrame) -> dict[str, pd.DataFrame]:
    comercial = limpo[limpo["commercial_game"]].copy()
    taxa_base = comercial["success"].mean()

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

    return {
        "cleaned": limpo,
        "genres": resumo_expandido(comercial, "Genres", "Genre", taxa_base).query(
            "games >= @TAMANHO_MIN_GRUPO"
        ),
        "tags": resumo_expandido(comercial, "Tags", "Tag", taxa_base).query(
            "games >= @TAMANHO_MIN_GRUPO"
        ),
        "prices": resumir_grupos(comercial, ["price_band"], taxa_base),
        "play_modes": resumir_grupos(comercial, ["play_mode"], taxa_base),
        "platforms": resumir_grupos(comercial, ["platform_count"], taxa_base),
        "years": resumir_grupos(comercial, ["release_year"], taxa_base),
        "combinations": combinacoes[combinacoes["games"] >= TAMANHO_MIN_GRUPO].copy(),
        "correlations": correlacoes(comercial),
    }


def percentual(valor: float) -> str:
    return f"{valor:.1%}"


def numero_compacto(valor: float) -> str:
    if valor >= 1_000_000:
        return f"{valor / 1_000_000:.1f}M"
    if valor >= 1_000:
        return f"{valor / 1_000:.0f}K"
    return f"{valor:,.0f}"


def limpar_eixos(eixo: plt.Axes) -> None:
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.grid(axis="x", color="#e2e8f0", linewidth=0.8)
    eixo.set_axisbelow(True)


def grafico_barras_confianca(
    quadro: pd.DataFrame,
    coluna_rotulo: str,
    titulo: str,
    limite: int = 10,
) -> plt.Figure:
    grafico = quadro.head(limite).sort_values("success_rate")
    figura, eixo = plt.subplots(figsize=(9, 5.2))
    erros = np.vstack(
        [
            grafico["success_rate"] - grafico["ci_low"],
            grafico["ci_high"] - grafico["success_rate"],
        ]
    )
    eixo.barh(grafico[coluna_rotulo], grafico["success_rate"], color=DESTAQUE, alpha=0.9)
    eixo.errorbar(
        grafico["success_rate"],
        grafico[coluna_rotulo],
        xerr=erros,
        fmt="none",
        ecolor="#0f172a",
        capsize=3,
        linewidth=1,
    )
    eixo.xaxis.set_major_formatter(lambda valor, _: f"{valor:.0%}")
    eixo.set_xlabel("Taxa de sucesso comercial")
    eixo.set_title(titulo, loc="left", fontweight="bold")
    limpar_eixos(eixo)
    figura.tight_layout()
    return figura


def grafico_barras_taxa(
    quadro: pd.DataFrame,
    coluna_rotulo: str,
    titulo: str,
    base: float,
) -> plt.Figure:
    grafico = quadro.sort_values("success_rate")
    figura, eixo = plt.subplots(figsize=(8, 4.5))
    cores = [SUCESSO if valor >= base else NEUTRO for valor in grafico["success_rate"]]
    eixo.barh(grafico[coluna_rotulo].astype(str), grafico["success_rate"], color=cores)
    eixo.axvline(base, color=AVISO, linestyle="--", linewidth=1.5, label=f"Taxa-base: {base:.1%}")
    eixo.xaxis.set_major_formatter(lambda valor, _: f"{valor:.0%}")
    eixo.set_xlabel("Taxa de sucesso comercial")
    eixo.set_title(titulo, loc="left", fontweight="bold")
    eixo.legend(frameon=False)
    limpar_eixos(eixo)
    figura.tight_layout()
    return figura


def grafico_tendencia(anos: pd.DataFrame, base: float) -> plt.Figure:
    grafico = anos[(anos["release_year"] >= 2005) & (anos["games"] >= 100)].sort_values(
        "release_year"
    )
    figura, eixo = plt.subplots(figsize=(10, 4.5))
    eixo.plot(
        grafico["release_year"],
        grafico["success_rate"],
        color=DESTAQUE,
        marker="o",
        markersize=4,
        linewidth=2,
    )
    eixo.fill_between(
        grafico["release_year"],
        grafico["ci_low"],
        grafico["ci_high"],
        color=DESTAQUE,
        alpha=0.15,
    )
    eixo.axhline(base, color=AVISO, linestyle="--", linewidth=1.5)
    eixo.yaxis.set_major_formatter(lambda valor, _: f"{valor:.0%}")
    eixo.set_xlabel("Ano de lancamento")
    eixo.set_ylabel("Taxa de sucesso comercial")
    eixo.set_title("Taxa de sucesso por ano de lancamento", loc="left", fontweight="bold")
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.grid(axis="y", color="#e2e8f0", linewidth=0.8)
    figura.tight_layout()
    return figura


def grafico_combinacoes(quadro: pd.DataFrame, base: float) -> plt.Figure:
    grafico = quadro.head(30).copy()
    figura, eixo = plt.subplots(figsize=(10, 5.3))
    dispersao = eixo.scatter(
        grafico["games"],
        grafico["success_rate"],
        s=np.sqrt(grafico["games"]) * 12,
        c=grafico["lift_vs_baseline"],
        cmap="viridis",
        alpha=0.8,
        edgecolor="white",
        linewidth=0.8,
    )
    for _, linha in grafico.head(5).iterrows():
        eixo.annotate(
            f"{linha['Genre']} / {linha['price_band']}",
            (linha["games"], linha["success_rate"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )
    eixo.axhline(base, color=AVISO, linestyle="--", linewidth=1.5)
    eixo.yaxis.set_major_formatter(lambda valor, _: f"{valor:.0%}")
    eixo.set_xlabel("Quantidade de jogos comparaveis")
    eixo.set_ylabel("Taxa de sucesso comercial")
    eixo.set_title("Oportunidade versus tamanho da evidencia", loc="left", fontweight="bold")
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.grid(color="#e2e8f0", linewidth=0.8)
    barra_cores = figura.colorbar(dispersao, ax=eixo)
    barra_cores.set_label("Ganho em relacao a taxa-base")
    figura.tight_layout()
    return figura


def grafico_correlacoes(quadro: pd.DataFrame) -> plt.Figure:
    grafico = quadro[quadro["metric"] != "owners_midpoint"].sort_values(
        "spearman_correlation_with_log_owners"
    )
    figura, eixo = plt.subplots(figsize=(8, 4.5))
    eixo.barh(
        grafico["metric"].str.replace("_", " ").map(TRADUCAO_METRICAS),
        grafico["spearman_correlation_with_log_owners"],
        color=DESTAQUE,
    )
    eixo.set_xlabel("Correlacao de Spearman com proprietarios estimados")
    eixo.set_title("Variaveis associadas a quantidade de proprietarios", loc="left", fontweight="bold")
    limpar_eixos(eixo)
    figura.tight_layout()
    return figura


def renderizar_dashboard(dados: dict[str, pd.DataFrame], origem: str) -> None:
    limpo = dados["cleaned"]
    comercial = limpo[limpo["commercial_game"].astype(bool)].copy()
    base = comercial["success"].astype(bool).mean()
    limite_vendas = comercial["owners_midpoint"].quantile(0.80)

    st.title("Relatorio de Oportunidades para Novos Jogos na Steam")
    st.caption(f"Mesma analise do trabalho original, consumindo dados de {origem}.")

    with st.sidebar:
        st.header("Filtros de combinacoes")
        generos_selecionados = st.multiselect(
            "Generos",
            sorted(dados["combinations"]["Genre"].dropna().unique()),
            placeholder="Todos os generos",
        )
        precos_selecionados = st.multiselect(
            "Faixas de preco",
            dados["prices"]["price_band"].dropna().tolist(),
            placeholder="Todas as faixas de preco",
        )
        modos_selecionados = st.multiselect(
            "Modos de jogo",
            dados["play_modes"]["play_mode"].dropna().tolist(),
            placeholder="Todos os modos de jogo",
            format_func=lambda modo: TRADUCAO_MODOS.get(modo, modo),
        )
        plataformas_selecionadas = st.multiselect(
            "Quantidade de plataformas",
            sorted(dados["platforms"]["platform_count"].dropna().astype(int).unique()),
            placeholder="Todas as quantidades",
        )
        minimo_jogos = st.slider("Minimo de jogos comparaveis", 100, 1_000, 100, 50)

    filtrado = dados["combinations"].copy()
    if generos_selecionados:
        filtrado = filtrado[filtrado["Genre"].isin(generos_selecionados)]
    if precos_selecionados:
        filtrado = filtrado[filtrado["price_band"].isin(precos_selecionados)]
    if modos_selecionados:
        filtrado = filtrado[filtrado["play_mode"].isin(modos_selecionados)]
    if plataformas_selecionadas:
        filtrado = filtrado[filtrado["platform_count"].isin(plataformas_selecionadas)]
    filtrado = filtrado[filtrado["games"] >= minimo_jogos].sort_values(
        ["evidence_score", "success_rate"], ascending=False
    )

    melhor = filtrado.iloc[0] if not filtrado.empty else dados["combinations"].iloc[0]
    colunas_metricas = st.columns(5)
    colunas_metricas[0].metric("Jogos limpos", f"{len(limpo):,}")
    colunas_metricas[1].metric("Jogos pagos analisados", f"{len(comercial):,}")
    colunas_metricas[2].metric("Taxa-base de sucesso", percentual(base))
    colunas_metricas[3].metric("Limite de vendas altas", numero_compacto(limite_vendas))
    colunas_metricas[4].metric(
        "Melhor sucesso filtrado",
        percentual(melhor["success_rate"]),
        f"{melhor['lift_vs_baseline']:.2f}x a taxa-base",
    )

    st.subheader("Recomendacao executiva")
    st.success(
        "**Valide um jogo multijogador de RPG ou estrategia com preco entre US$ 10 e US$ 20, "
        "inicialmente desenvolvido para Windows.** Jogos multijogador, RPG e a faixa US$ 10-20 "
        "aparecem com evidencias historicas acima da media."
    )
    st.info(
        f"Melhor combinacao para os filtros selecionados: **{melhor['Genre']} / "
        f"{melhor['price_band']} / {TRADUCAO_MODOS.get(melhor['play_mode'], melhor['play_mode'])} / "
        f"{int(melhor['platform_count'])} plataforma(s)**, com "
        f"**{percentual(melhor['success_rate'])} de sucesso** em "
        f"**{int(melhor['games']):,} jogos comparaveis**."
    )

    aba_visao_geral, aba_oportunidades, aba_mercado, aba_metodologia = st.tabs(
        ["Visao executiva", "Explorador de oportunidades", "Evidencias de mercado", "Metodologia"]
    )

    with aba_visao_geral:
        esquerda, direita = st.columns(2)
        with esquerda:
            st.pyplot(
                grafico_barras_confianca(dados["genres"], "Genre", "Principais generos por evidencia"),
                width="stretch",
            )
        with direita:
            st.pyplot(
                grafico_barras_taxa(
                    dados["prices"], "price_band", "Taxa de sucesso por faixa de preco", base
                ),
                width="stretch",
            )

        esquerda, direita = st.columns(2)
        with esquerda:
            st.pyplot(
                grafico_barras_taxa(
                    dados["play_modes"].assign(
                        play_mode=dados["play_modes"]["play_mode"].map(TRADUCAO_MODOS)
                    ),
                    "play_mode",
                    "Oportunidade de jogos multijogador",
                    base,
                ),
                width="stretch",
            )
        with direita:
            st.pyplot(
                grafico_barras_taxa(
                    dados["platforms"],
                    "platform_count",
                    "Taxa de sucesso por cobertura de plataformas",
                    base,
                ),
                width="stretch",
            )

    with aba_oportunidades:
        if filtrado.empty:
            st.warning("Nenhuma combinacao corresponde aos filtros selecionados.")
        else:
            st.pyplot(grafico_combinacoes(filtrado, base), width="stretch")
            tabela_exibicao = filtrado[
                [
                    "Genre",
                    "price_band",
                    "play_mode",
                    "platform_count",
                    "games",
                    "success_rate",
                    "lift_vs_baseline",
                    "ci_low",
                    "ci_high",
                    "median_price",
                ]
            ].rename(
                columns={
                    "Genre": "Genero",
                    "price_band": "Faixa de preco",
                    "play_mode": "Modo de jogo",
                    "platform_count": "Plataformas",
                    "games": "Jogos",
                    "success_rate": "Taxa de sucesso",
                    "lift_vs_baseline": "Ganho sobre a taxa-base",
                    "ci_low": "Limite inferior",
                    "ci_high": "Limite superior",
                    "median_price": "Preco mediano",
                }
            )
            tabela_exibicao["Modo de jogo"] = tabela_exibicao["Modo de jogo"].map(TRADUCAO_MODOS)
            st.dataframe(
                tabela_exibicao.style.format(
                    {
                        "Taxa de sucesso": "{:.1%}",
                        "Ganho sobre a taxa-base": "{:.2f}x",
                        "Limite inferior": "{:.1%}",
                        "Limite superior": "{:.1%}",
                        "Preco mediano": "US$ {:.2f}",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

    with aba_mercado:
        esquerda, direita = st.columns(2)
        with esquerda:
            st.pyplot(
                grafico_barras_confianca(dados["tags"], "Tag", "Principais tags por evidencia"),
                width="stretch",
            )
        with direita:
            st.pyplot(grafico_correlacoes(dados["correlations"]), width="stretch")
        st.pyplot(grafico_tendencia(dados["years"], base), width="stretch")

    with aba_metodologia:
        st.markdown(
            f"""
            ### Definicao de sucesso

            Um jogo e classificado como comercialmente bem-sucedido quando:

            - E pago e custa no maximo US$ 100.
            - Esta entre os 20% dos jogos pagos com mais proprietarios estimados.
            - Possui pelo menos **{numero_compacto(limite_vendas)} proprietarios estimados**.
            - Possui pelo menos 20 avaliacoes.
            - Possui pelo menos 75% de avaliacoes positivas.

            ### Fonte desta versao

            Esta copia do app monta o mesmo DataFrame analitico a partir de **{origem}**.
            Os graficos e a pergunta de negocio permanecem os mesmos do trabalho original.
            """
        )
