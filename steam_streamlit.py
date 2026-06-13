from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


DIRETORIO_BASE = Path(__file__).resolve().parent
DIRETORIO_DADOS = DIRETORIO_BASE / "steam_analysis"
DESTAQUE = "#2563eb"
SUCESSO = "#16a34a"
NEUTRO = "#94a3b8"
AVISO = "#d97706"

TRADUCAO_MODOS = {
    "Has multiplayer": "Possui multijogador",
    "Single-player only": "Somente um jogador",
    "Unspecified": "Não especificado",
}

TRADUCAO_METRICAS = {
    "price usd": "Preço",
    "peak ccu": "Pico de jogadores simultâneos",
    "review count": "Quantidade de avaliações",
    "positive ratio": "Proporção de avaliações positivas",
    "recommendations": "Recomendações",
    "avg playtime minutes": "Tempo médio de jogo",
    "metacritic score": "Nota Metacritic",
    "platform count": "Quantidade de plataformas",
}


st.set_page_config(
    page_title="Relatório de Oportunidades para Jogos na Steam",
    page_icon="",
    layout="wide",
)


@st.cache_data
def carregar_dados() -> dict[str, pd.DataFrame]:
    arquivos = {
        "cleaned": "steam_cleaned.csv",
        "genres": "genres.csv",
        "tags": "tags.csv",
        "combinations": "combinations.csv",
        "prices": "price_bands.csv",
        "play_modes": "play_modes.csv",
        "platforms": "platforms.csv",
        "years": "release_years.csv",
        "correlations": "correlations.csv",
    }
    ausentes = [nome for nome in arquivos.values() if not (DIRETORIO_DADOS / nome).exists()]
    if ausentes:
        raise FileNotFoundError(
            f"Arquivos de análise ausentes: {', '.join(ausentes)}. Execute `python steam_calculo.py`."
        )
    return {chave: pd.read_csv(DIRETORIO_DADOS / nome_arquivo) for chave, nome_arquivo in arquivos.items()}


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
    eixo.axvline(
        base,
        color=AVISO,
        linestyle="--",
        linewidth=1.5,
        label=f"Taxa-base: {base:.1%}",
    )
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
        grafico["release_year"], grafico["ci_low"], grafico["ci_high"], color=DESTAQUE, alpha=0.15
    )
    eixo.axhline(base, color=AVISO, linestyle="--", linewidth=1.5)
    eixo.yaxis.set_major_formatter(lambda valor, _: f"{valor:.0%}")
    eixo.set_xlabel("Ano de lançamento")
    eixo.set_ylabel("Taxa de sucesso comercial")
    eixo.set_title("Taxa de sucesso por ano de lançamento", loc="left", fontweight="bold")
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
    eixo.set_xlabel("Quantidade de jogos comparáveis")
    eixo.set_ylabel("Taxa de sucesso comercial")
    eixo.set_title("Oportunidade versus tamanho da evidência", loc="left", fontweight="bold")
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.grid(color="#e2e8f0", linewidth=0.8)
    barra_cores = figura.colorbar(dispersao, ax=eixo)
    barra_cores.set_label("Ganho em relação à taxa-base")
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
    eixo.set_xlabel("Correlação de Spearman com proprietários estimados")
    eixo.set_title("Variáveis associadas à quantidade de proprietários", loc="left", fontweight="bold")
    limpar_eixos(eixo)
    figura.tight_layout()
    return figura


try:
    dados = carregar_dados()
except FileNotFoundError as erro:
    st.error(str(erro))
    st.stop()

limpo = dados["cleaned"]
comercial = limpo[limpo["commercial_game"].astype(bool)].copy()
base = comercial["success"].astype(bool).mean()
limite_vendas = comercial["owners_midpoint"].quantile(0.80)

st.title("Relatório de Oportunidades para Novos Jogos na Steam")
st.caption(
    "Orientação de conceito e posicionamento baseada em evidências do mercado da Steam"
)

with st.sidebar:
    st.header("Filtros de combinações")
    generos_selecionados = st.multiselect(
        "Gêneros",
        sorted(dados["combinations"]["Genre"].dropna().unique()),
        placeholder="Todos os gêneros",
    )
    precos_selecionados = st.multiselect(
        "Faixas de preço",
        dados["prices"]["price_band"].dropna().tolist(),
        placeholder="Todas as faixas de preço",
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
    minimo_jogos = st.slider("Mínimo de jogos comparáveis", 100, 1_000, 100, 50)
    st.divider()
    st.caption(
        "Sucesso = jogo pago entre os 20% com mais proprietários estimados, com pelo menos "
        "20 avaliações e 75% de avaliações positivas."
    )

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

st.subheader("Recomendação executiva")
st.success(
    "**Valide um jogo multijogador de RPG ou estratégia com preço entre US$ 10 e US$ 20, "
    "inicialmente desenvolvido para Windows.** Jogos multijogador apresentam um ganho de "
    f"**{dados['play_modes'].iloc[0]['lift_vs_baseline']:.2f}x** na taxa de sucesso. "
    "RPG é o gênero amplo mais forte e US$ 10-20 é a faixa de preço com melhor evidência "
    "em uma amostra grande."
)
st.info(
    f"Melhor combinação para os filtros selecionados: **{melhor['Genre']} / "
    f"{melhor['price_band']} / {TRADUCAO_MODOS.get(melhor['play_mode'], melhor['play_mode'])} / "
    f"{int(melhor['platform_count'])} plataforma(s)**, com "
    f"**{percentual(melhor['success_rate'])} de sucesso** em "
    f"**{int(melhor['games']):,} jogos comparáveis**."
)

aba_visao_geral, aba_oportunidades, aba_mercado, aba_metodologia = st.tabs(
    ["Visão executiva", "Explorador de oportunidades", "Evidências de mercado", "Metodologia"]
)

with aba_visao_geral:
    esquerda, direita = st.columns(2)
    with esquerda:
        st.pyplot(
            grafico_barras_confianca(dados["genres"], "Genre", "Principais gêneros por evidência"),
            width="stretch",
        )
    with direita:
        st.pyplot(
            grafico_barras_taxa(
                dados["prices"], "price_band", "Taxa de sucesso por faixa de preço", base
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
        st.warning("Nenhuma combinação corresponde aos filtros selecionados.")
    else:
        st.pyplot(grafico_combinacoes(filtrado, base), width="stretch")
        colunas_exibicao = {
            "Genre": "Gênero",
            "price_band": "Faixa de preço",
            "play_mode": "Modo de jogo",
            "platform_count": "Plataformas",
            "games": "Jogos",
            "success_rate": "Taxa de sucesso",
            "lift_vs_baseline": "Ganho sobre a taxa-base",
            "ci_low": "Limite inferior",
            "ci_high": "Limite superior",
            "median_price": "Preço mediano",
        }
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
        ].rename(columns=colunas_exibicao)
        tabela_exibicao["Modo de jogo"] = tabela_exibicao["Modo de jogo"].map(TRADUCAO_MODOS)
        st.dataframe(
            tabela_exibicao.style.format(
                {
                    "Taxa de sucesso": "{:.1%}",
                    "Ganho sobre a taxa-base": "{:.2f}x",
                    "Limite inferior": "{:.1%}",
                    "Limite superior": "{:.1%}",
                    "Preço mediano": "US$ {:.2f}",
                }
            ),
            width="stretch",
            hide_index=True,
        )
        st.download_button(
            "Baixar combinações filtradas",
            filtrado.to_csv(index=False),
            "oportunidades_de_jogos_filtradas.csv",
            "text/csv",
        )

with aba_mercado:
    esquerda, direita = st.columns(2)
    with esquerda:
        st.pyplot(
            grafico_barras_confianca(dados["tags"], "Tag", "Principais tags por evidência"),
            width="stretch",
        )
        st.caption(
            "Tags como Classic e Cult Classic representam resultados retrospectivos, "
            "não requisitos confiáveis para um novo conceito."
        )
    with direita:
        st.pyplot(grafico_correlacoes(dados["correlations"]), width="stretch")
        st.caption("Correlação indica associação, não causalidade.")

    st.pyplot(grafico_tendencia(dados["years"], base), width="stretch")

with aba_metodologia:
    st.markdown(
        f"""
        ### Definição de sucesso

        Um jogo é classificado como comercialmente bem-sucedido quando:

        - É pago e custa no máximo US$ 100
        - Está entre os 20% dos jogos pagos com mais proprietários estimados
        - Possui pelo menos **{numero_compacto(limite_vendas)} proprietários estimados**
        - Possui pelo menos 20 avaliações
        - Possui pelo menos 75% de avaliações positivas

        ### Abordagem estatística

        - A quantidade de proprietários usa o ponto médio da faixa estimada pela Steam.
        - Os rankings usam o ganho na taxa de sucesso e o limite inferior de um intervalo de confiança de Wilson de 95%.
        - Os grupos exigem pelo menos 100 jogos comparáveis para reduzir ruídos de amostras pequenas.
        - A correlação de Spearman mede a associação monotônica com a quantidade de proprietários.

        ### Limitações importantes

        - O conjunto de dados não inclui custo de desenvolvimento nem investimento em marketing.
        - A cobertura de plataformas pode ser consequência do sucesso, em vez de sua causa.
        - Os preços atuais podem ser diferentes dos preços de lançamento.
        - Evidências observacionais de mercado não provam que uma característica causa sucesso.
        """
    )
    st.download_button(
        "Baixar conjunto de dados analítico limpo",
        limpo.to_csv(index=False),
        "steam_dados_limpos.csv",
        "text/csv",
    )
