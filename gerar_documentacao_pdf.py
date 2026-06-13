from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd


BASE = Path(__file__).resolve().parent
SAIDA = BASE / "documentacao_tecnica_steam.pdf"
DADOS = BASE / "steam_analysis"

AZUL = "#1d4ed8"
AZUL_CLARO = "#dbeafe"
VERDE = "#15803d"
CINZA = "#475569"
FUNDO = "#f8fafc"
LARANJA = "#c2410c"


def pagina_base(titulo, subtitulo=None):
    figura = plt.figure(figsize=(8.27, 11.69), facecolor="white")
    figura.text(0.07, 0.955, titulo, fontsize=19, fontweight="bold", color=AZUL)
    if subtitulo:
        figura.text(0.07, 0.925, subtitulo, fontsize=9.5, color=CINZA)
    figura.add_artist(
        plt.Line2D([0.07, 0.93], [0.91, 0.91], transform=figura.transFigure, color=AZUL, linewidth=1.2)
    )
    return figura


def escrever_bloco(figura, texto, y, tamanho=9.5, largura=104, cor="#0f172a", espacamento=0.0205):
    linhas = []
    for paragrafo in texto.strip().split("\n"):
        if not paragrafo.strip():
            linhas.append("")
        else:
            linhas.extend(textwrap.wrap(paragrafo, width=largura, replace_whitespace=False))
    for linha in linhas:
        figura.text(0.075, y, linha, fontsize=tamanho, color=cor, va="top", family="DejaVu Sans")
        y -= espacamento
    return y


def pagina_texto(pdf, titulo, secoes, subtitulo=None):
    figura = pagina_base(titulo, subtitulo)
    y = 0.885
    for cabecalho, corpo in secoes:
        figura.text(0.075, y, cabecalho, fontsize=12, fontweight="bold", color=VERDE, va="top")
        y -= 0.027
        y = escrever_bloco(figura, corpo, y)
        y -= 0.016
    pdf.savefig(figura, bbox_inches="tight")
    plt.close(figura)


def pagina_codigo(pdf, titulo, descricao, codigo):
    figura = pagina_base(titulo)
    y = escrever_bloco(figura, descricao, 0.88, tamanho=9.5)
    y -= 0.015
    caixa = plt.Rectangle((0.065, 0.08), 0.87, y - 0.08, transform=figura.transFigure, color="#0f172a")
    figura.add_artist(caixa)
    linhas = codigo.strip().splitlines()
    altura = min(8.0, max(6.3, 8.4 - max(0, len(linhas) - 24) * 0.07))
    figura.text(
        0.085,
        y - 0.018,
        codigo.strip(),
        fontsize=altura,
        color="#e2e8f0",
        va="top",
        family="DejaVu Sans Mono",
        linespacing=1.32,
    )
    pdf.savefig(figura, bbox_inches="tight")
    plt.close(figura)


def pagina_tabela(pdf, titulo, descricao, quadro, formatos=None):
    figura = pagina_base(titulo)
    escrever_bloco(figura, descricao, 0.88, tamanho=9.3)
    eixo = figura.add_axes([0.06, 0.13, 0.88, 0.62])
    eixo.axis("off")
    exibicao = quadro.copy()
    formatos = formatos or {}
    for coluna, formato in formatos.items():
        exibicao[coluna] = exibicao[coluna].map(formato)
    tabela = eixo.table(
        cellText=exibicao.values,
        colLabels=exibicao.columns,
        cellLoc="center",
        colLoc="center",
        loc="center",
    )
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(7.7)
    tabela.scale(1, 1.55)
    for (linha, coluna), celula in tabela.get_celld().items():
        if linha == 0:
            celula.set_facecolor(AZUL)
            celula.set_text_props(color="white", fontweight="bold")
        elif linha % 2 == 0:
            celula.set_facecolor(AZUL_CLARO)
        celula.set_edgecolor("white")
    pdf.savefig(figura, bbox_inches="tight")
    plt.close(figura)


def pagina_fluxo(pdf):
    figura = pagina_base("Arquitetura completa do projeto", "Fluxo entre origem, processamento, arquivos analíticos e dashboard")
    eixo = figura.add_axes([0.06, 0.12, 0.88, 0.72])
    eixo.axis("off")
    caixas = [
        (0.03, 0.69, 0.22, 0.16, "steam_dataset.csv\nFonte bruta", LARANJA),
        (0.38, 0.69, 0.24, 0.16, "steam_calculo.py\nReparo + limpeza", AZUL),
        (0.73, 0.69, 0.24, 0.16, "steam_cleaned.csv\nBase analítica", VERDE),
        (0.20, 0.35, 0.25, 0.18, "CSVs estatísticos\nGêneros, tags, preços,\nmodos, plataformas...", VERDE),
        (0.58, 0.35, 0.25, 0.18, "steam_streamlit.py\nLeitura + filtros + gráficos", AZUL),
        (0.38, 0.04, 0.25, 0.16, "Dashboard Streamlit\nRelatório de negócio", LARANJA),
    ]
    for x, y, w, h, texto, cor in caixas:
        eixo.add_patch(plt.Rectangle((x, y), w, h, facecolor=cor, alpha=0.92, edgecolor="none"))
        eixo.text(x + w / 2, y + h / 2, texto, color="white", ha="center", va="center", fontsize=9, fontweight="bold")
    setas = [
        ((0.25, 0.77), (0.38, 0.77)),
        ((0.62, 0.77), (0.73, 0.77)),
        ((0.50, 0.69), (0.34, 0.53)),
        ((0.45, 0.44), (0.58, 0.44)),
        ((0.705, 0.35), (0.505, 0.20)),
        ((0.85, 0.69), (0.75, 0.53)),
    ]
    for inicio, fim in setas:
        eixo.annotate("", xy=fim, xytext=inicio, arrowprops={"arrowstyle": "->", "color": CINZA, "lw": 2})
    figura.text(
        0.075,
        0.075,
        "Separação de responsabilidades: o primeiro script prepara dados e estatísticas; o segundo interpreta e apresenta os resultados.",
        fontsize=9.5,
        color=CINZA,
    )
    pdf.savefig(figura, bbox_inches="tight")
    plt.close(figura)


def pagina_graficos_resultados(pdf, generos, precos, modos):
    figura = pagina_base("Resultados usados pelo dashboard", "Exemplos reais produzidos pelo pipeline atual")
    e1 = figura.add_axes([0.10, 0.60, 0.82, 0.24])
    g = generos.head(7).sort_values("success_rate")
    e1.barh(g["Genre"], g["success_rate"], color=AZUL)
    e1.set_title("Taxa de sucesso por gênero", loc="left", fontweight="bold")
    e1.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    e1.spines[["top", "right"]].set_visible(False)

    e2 = figura.add_axes([0.10, 0.33, 0.82, 0.20])
    p = precos.sort_values("success_rate")
    e2.barh(p["price_band"], p["success_rate"], color=VERDE)
    e2.set_title("Taxa de sucesso por faixa de preço", loc="left", fontweight="bold")
    e2.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    e2.spines[["top", "right"]].set_visible(False)

    e3 = figura.add_axes([0.10, 0.08, 0.82, 0.17])
    m = modos.sort_values("success_rate")
    e3.barh(m["play_mode"], m["success_rate"], color=LARANJA)
    e3.set_title("Taxa de sucesso por modo de jogo", loc="left", fontweight="bold")
    e3.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    e3.spines[["top", "right"]].set_visible(False)
    pdf.savefig(figura, bbox_inches="tight")
    plt.close(figura)


def gerar():
    limpo = pd.read_csv(DADOS / "steam_cleaned.csv")
    comercial = limpo[limpo["commercial_game"].astype(bool)]
    generos = pd.read_csv(DADOS / "genres.csv")
    precos = pd.read_csv(DADOS / "price_bands.csv")
    modos = pd.read_csv(DADOS / "play_modes.csv")
    combinacoes = pd.read_csv(DADOS / "combinations.csv")
    correlacoes = pd.read_csv(DADOS / "correlations.csv")
    taxa_base = comercial["success"].astype(bool).mean()
    limite_vendas = comercial["owners_midpoint"].quantile(0.80)

    with PdfPages(SAIDA) as pdf:
        figura = plt.figure(figsize=(8.27, 11.69), facecolor=FUNDO)
        figura.text(0.08, 0.79, "Documentação técnica detalhada", fontsize=25, fontweight="bold", color=AZUL)
        figura.text(0.08, 0.735, "Pipeline estatístico Steam e dashboard Streamlit", fontsize=16, color=VERDE)
        figura.text(0.08, 0.65, "Arquivos documentados:", fontsize=11, fontweight="bold", color=CINZA)
        figura.text(0.10, 0.61, "steam_calculo.py", fontsize=13, family="DejaVu Sans Mono")
        figura.text(0.10, 0.575, "steam_streamlit.py", fontsize=13, family="DejaVu Sans Mono")
        figura.text(0.08, 0.46, "Objetivo", fontsize=13, fontweight="bold", color=VERDE)
        escrever_bloco(
            figura,
            "Explicar detalhadamente todas as decisões implementadas: reparo do CSV, limpeza, criação de variáveis, definição de sucesso, estatísticas, arquivos gerados, visualizações, filtros, interpretação e limitações.",
            0.425,
            tamanho=10.5,
            largura=82,
            espacamento=0.025,
        )
        figura.text(0.08, 0.20, "Gerado em 12 de junho de 2026", fontsize=10, color=CINZA)
        pdf.savefig(figura, bbox_inches="tight")
        plt.close(figura)

        pagina_texto(pdf, "Resumo executivo do trabalho realizado", [
            ("Resultado geral", f"O projeto foi dividido em duas responsabilidades. O arquivo steam_calculo.py transforma o CSV bruto em uma base limpa e em tabelas estatísticas reutilizáveis. O arquivo steam_streamlit.py consome essas tabelas e apresenta a análise de negócio em um dashboard interativo com Matplotlib."),
            ("Números atuais", f"O pipeline reteve {len(limpo):,} jogos limpos, identificou {len(comercial):,} jogos comerciais pagos e classificou {int(comercial['success'].astype(bool).sum()):,} como sucesso. O limite de vendas altas é {limite_vendas:,.0f} proprietários estimados e a taxa-base de sucesso é {taxa_base:.2%}."),
            ("Princípio de projeto", "A análise de negócio foi retirada do script de processamento. Assim, o pipeline fica responsável por fatos, métricas e arquivos; o Streamlit fica responsável por interpretação, recomendações, visualização e interação."),
        ])

        pagina_fluxo(pdf)

        pagina_texto(pdf, "1. Problema de qualidade encontrado no CSV", [
            ("Defeito estrutural", "O arquivo original possui linhas sem o valor AppID e um cabeçalho combinado chamado DiscountDLC count. Por isso, as primeiras colunas são lidas em posições erradas: o nome aparece em AppID, a data aparece em Name, a faixa de proprietários aparece em Release date e assim por diante até Price."),
            ("Como foi diagnosticado", "Foi comparado o cabeçalho com exemplos reais. Um registro mostrava AppID = nome do jogo, Name = data e Release date = faixa de proprietários. A partir de About the game, o segundo defeito do cabeçalho recompõe o alinhamento."),
            ("Solução", "COLUNAS_DESLOCADAS funciona como contrato de reparo. carregar_e_reparar lê somente as colunas necessárias e cria um novo DataFrame com os nomes corretos. O AppID real não pode ser recuperado porque ele não está presente nas linhas."),
            ("Impacto", "Sem esse reparo, preço, proprietários, pico de jogadores e idade seriam interpretados incorretamente. Qualquer conclusão estatística seria inválida."),
        ])

        pagina_codigo(pdf, "2. Constantes e reparo da origem", "As constantes centralizam caminhos, data de corte e critérios mínimos. O mapeamento abaixo documenta explicitamente onde cada campo correto foi encontrado no CSV defeituoso.", """
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
    "Genres": "Genres",
    "Tags": "Tags",
}

def carregar_e_reparar():
    colunas_brutas = list(dict.fromkeys(COLUNAS_DESLOCADAS.values()))
    bruto = pd.read_csv(FONTE, usecols=colunas_brutas, low_memory=False)
    return pd.DataFrame({
        correto: bruto[deslocado]
        for correto, deslocado in COLUNAS_DESLOCADAS.items()
    })
""")

        pagina_texto(pdf, "3. Limpeza: datas, proprietários e números", [
            ("Datas", "Release date é convertida com pd.to_datetime(errors='coerce'). Valores inválidos tornam-se NaT e são removidos posteriormente. A DATA_ANALISE impede que lançamentos futuros entrem na comparação."),
            ("Faixas de proprietários", "Estimated owners tem formato como 0 - 20000. Uma expressão regular extrai os limites inferior e superior. O pipeline cria owners_lower, owners_upper e owners_midpoint. O ponto médio é usado como aproximação numérica para vendas."),
            ("Conversão numérica", "A função numerico usa pd.to_numeric(errors='coerce'). Isso padroniza Peak CCU, idade, preço, Metacritic, avaliações, recomendações e tempo médio. Valores impossíveis tornam-se ausentes em vez de interromper a execução."),
            ("Limitação importante", "O ponto médio de uma faixa ampla não é uma contagem exata. Ele permite comparações e agrupamentos, mas não deve ser tratado como receita real."),
        ])

        pagina_texto(pdf, "4. Variáveis derivadas", [
            ("Avaliações", "review_count soma avaliações positivas e negativas. positive_ratio divide positivas pelo total somente quando existe ao menos uma avaliação."),
            ("Plataformas", "platform_count soma os indicadores booleanos Windows, Mac e Linux. O valor varia de zero a três."),
            ("Faixa de preço", "price_band agrupa preço em Free, $0-5, $5-10, $10-20, $20-30, $30-60 e $60+. Isso reduz ruído e permite comparar posicionamentos comerciais."),
            ("Ano de lançamento", "release_year é extraído de release_date e alimenta a análise temporal no dashboard."),
            ("Modo de jogo", "play_mode procura textos de multiplayer e single-player em Categories. Multiplayer tem prioridade quando ambas as expressões aparecem. Sem evidência, o registro recebe Unspecified."),
        ])

        pagina_texto(pdf, "5. Filtros e exclusões", [
            ("Itens não comparáveis", "O texto combinado de nome, categorias, gêneros e tags é pesquisado por playtest, demo, soundtrack, server, benchmark e editor. Esses itens não representam um jogo comercial completo e são removidos."),
            ("Validade mínima", "Um registro precisa possuir data válida, não estar no futuro, possuir ponto médio de proprietários, possuir gênero e não estar marcado como item excluído."),
            ("Duplicatas", "drop_duplicates usa Name, release_date e Developers. Essa chave evita contar novamente o mesmo jogo do mesmo desenvolvedor e lançamento."),
            ("Resultado", f"A base limpa atual contém {len(limpo):,} registros, cobrindo lançamentos entre {int(limpo['release_year'].min())} e {int(limpo['release_year'].max())}."),
        ])

        pagina_texto(pdf, "6. Definição estatística de sucesso", [
            ("Jogo comercial", "commercial_game é verdadeiro quando o preço é maior que zero e menor ou igual a US$ 100. Jogos gratuitos são analisáveis na base limpa, mas não participam do ranking comercial."),
            ("Vendas altas", f"high_sales exige owners_midpoint acima ou igual ao percentil 80 dos jogos pagos. No conjunto atual, esse limite é {limite_vendas:,.0f} proprietários estimados."),
            ("Boa avaliação", "well_rated exige pelo menos 20 avaliações e positive_ratio de no mínimo 75%. O mínimo reduz casos em que uma ou duas avaliações positivas criariam uma nota enganosa."),
            ("Sucesso final", "success = commercial_game AND high_sales AND well_rated. Portanto, sucesso combina alcance comercial e evidência mínima de satisfação."),
            ("Taxa-base", f"Entre os {len(comercial):,} jogos pagos analisados, {int(comercial['success'].astype(bool).sum()):,} atendem aos critérios. A taxa-base é {taxa_base:.2%}."),
        ])

        pagina_codigo(pdf, "7. Intervalo de confiança de Wilson", "A taxa observada isolada pode favorecer grupos pequenos. O intervalo de Wilson estima uma faixa plausível para a taxa real de sucesso. O projeto usa z = 1,96, correspondente a aproximadamente 95% de confiança.", """
def intervalo_wilson(sucessos, total):
    z = 1.96
    taxa = sucessos / total
    denominador = 1 + z**2 / total
    centro = (taxa + z**2 / (2 * total)) / denominador
    margem = (
        z
        * np.sqrt(
            (taxa * (1 - taxa) + z**2 / (4 * total)) / total
        )
        / denominador
    )
    return centro - margem, centro + margem

ci_low, ci_high = intervalo_wilson(successes, games)
""")

        pagina_texto(pdf, "8. Resumo por grupos e evidence_score", [
            ("Agregações", "resumir_grupos calcula quantidade de jogos, quantidade de sucessos, taxa de sucesso, medianas de proprietários, preço, proporção positiva e avaliações."),
            ("Lift", "lift_vs_baseline = success_rate / taxa_base. Um lift de 1,50 significa taxa de sucesso 50% superior à média dos jogos pagos analisados."),
            ("Evidence score", "evidence_score = ci_low × log(1 + games). A parte ci_low favorece resultados cujo limite inferior ainda é forte. O logaritmo recompensa amostras maiores sem permitir que o volume domine completamente."),
            ("Ordenação", "As tabelas são ordenadas primeiro por evidence_score, depois por success_rate e games. Portanto, o primeiro item representa combinação de desempenho e robustez, não apenas a maior porcentagem."),
        ])

        pagina_texto(pdf, "9. Campos multivalorados e correlações", [
            ("Explosão de gêneros, tags e categorias", "Um jogo pode possuir vários valores separados por vírgula. resumo_expandido divide a string em lista, remove espaços, usa explode e cria uma linha analítica por valor. Assim, um jogo RPG/Adventure participa dos dois resumos."),
            ("Correlação de Spearman", "correlacoes mede associação monotônica entre proprietários e preço, pico CCU, avaliações, proporção positiva, recomendações, tempo médio, Metacritic e quantidade de plataformas."),
            ("Transformação logarítmica", "Variáveis de volume recebem log1p porque distribuições de proprietários e avaliações são extremamente assimétricas. A transformação reduz a influência visual e numérica de grandes outliers."),
            ("Cuidado", "Correlação não demonstra causalidade. Mais avaliações podem acompanhar mais vendas porque mais compradores geram avaliações; isso não prova que avaliações causam vendas."),
        ])

        arquivos = pd.DataFrame([
            ["steam_cleaned.csv", f"{len(limpo):,}", "Base limpa por jogo"],
            ["genres.csv", f"{len(generos):,}", "Resumo por gênero"],
            ["tags.csv", f"{len(pd.read_csv(DADOS / 'tags.csv')):,}", "Resumo por tag"],
            ["categories.csv", f"{len(pd.read_csv(DADOS / 'categories.csv')):,}", "Resumo por categoria"],
            ["price_bands.csv", f"{len(precos):,}", "Resumo por faixa de preço"],
            ["play_modes.csv", f"{len(modos):,}", "Resumo por modo de jogo"],
            ["platforms.csv", f"{len(pd.read_csv(DADOS / 'platforms.csv')):,}", "Resumo por plataformas"],
            ["release_years.csv", f"{len(pd.read_csv(DADOS / 'release_years.csv')):,}", "Resumo por ano"],
            ["combinations.csv", f"{len(combinacoes):,}", "Gênero + preço + modo + plataformas"],
            ["correlations.csv", f"{len(correlacoes):,}", "Correlações com proprietários"],
        ], columns=["Arquivo", "Linhas", "Finalidade"])
        pagina_tabela(pdf, "10. Arquivos gerados por steam_calculo.py", "Todos os arquivos abaixo são gravados em steam_analysis/. O Streamlit depende deles, exceto categories.csv, que permanece disponível para análises adicionais.", arquivos)

        pagina_texto(pdf, "11. Função principal do pipeline", [
            ("Orquestração", "principal cria o diretório, repara a origem, limpa os dados, separa jogos pagos e calcula a taxa-base."),
            ("Tabelas simples", "São produzidos resumos por gênero, tag, categoria, faixa de preço, modo de jogo, quantidade de plataformas e ano."),
            ("Combinações", "O gênero é expandido e agrupado com price_band, play_mode e platform_count. Combinações com menos de 100 jogos são removidas para limitar conclusões frágeis."),
            ("Persistência", "steam_cleaned.csv e cada tabela estatística são exportados. O script não contém recomendações de negócio; ele termina com um resumo curto de processamento."),
            ("Execução", "Comando: python steam_calculo.py. Deve ser executado novamente quando steam_dataset.csv ou os critérios estatísticos mudarem."),
        ])

        pagina_texto(pdf, "12. Estrutura do dashboard Streamlit", [
            ("Responsabilidade", "steam_streamlit.py apresenta a camada de negócio. Ele não recalcula todo o pipeline; lê os CSVs prontos, aplica filtros de interface e constrói gráficos."),
            ("Configuração", "st.set_page_config define título e layout amplo. As constantes de cor padronizam azul de destaque, verde de sucesso, cinza neutro e laranja de referência."),
            ("Cache", "carregar_dados usa @st.cache_data. Após a primeira leitura, o Streamlit pode reutilizar os DataFrames e responder mais rapidamente às interações."),
            ("Proteção contra ausência", "Antes de carregar, a função confirma que todos os arquivos necessários existem. Se faltarem arquivos, mostra orientação para executar python steam_calculo.py e interrompe o app."),
        ])

        pagina_texto(pdf, "13. Funções de visualização Matplotlib", [
            ("limpar_eixos", "Remove bordas superior e direita, adiciona grade horizontal e mantém os dados acima da grade. Isso cria identidade visual consistente."),
            ("grafico_barras_confianca", "Exibe taxa de sucesso por gênero ou tag e adiciona barras de erro calculadas a partir de ci_low e ci_high."),
            ("grafico_barras_taxa", "Compara grupos com a taxa-base. Barras acima da média ficam verdes; abaixo da média ficam cinza; a referência é uma linha laranja."),
            ("grafico_tendencia", "Mostra a taxa por ano desde 2005, apenas com anos que possuem pelo menos 100 jogos. A área translúcida representa o intervalo de confiança."),
            ("grafico_combinacoes", "Relaciona tamanho da amostra e taxa de sucesso. Tamanho da bolha depende da quantidade de jogos; cor depende do lift; cinco oportunidades recebem rótulo."),
            ("grafico_correlacoes", "Apresenta associações de Spearman com proprietários estimados e remove owners_midpoint, que teria correlação perfeita consigo mesmo."),
        ])

        pagina_texto(pdf, "14. Sidebar, filtros e seleção da melhor oportunidade", [
            ("Filtros", "A barra lateral permite escolher gêneros, faixas de preço, modos de jogo, quantidade de plataformas e mínimo de jogos comparáveis."),
            ("Aplicação progressiva", "Cada filtro selecionado reduz combinations.csv. Depois, o mínimo de jogos é aplicado e os resultados são ordenados por evidence_score e success_rate."),
            ("Fallback", "Se nenhum filtro estiver ativo, o melhor resultado geral é usado. Se uma combinação de filtros não retornar linhas, o dashboard mostra aviso em vez de falhar."),
            ("Indicadores", "Cinco métricas exibem jogos limpos, jogos pagos, taxa-base, limite de vendas altas e taxa da melhor combinação filtrada."),
            ("Interpretação", "A recomendação executiva é deliberadamente apresentada no Streamlit, pois esta camada é responsável por comunicação de negócio."),
        ])

        pagina_texto(pdf, "15. Abas do relatório de negócio", [
            ("Executive overview", "Mostra gêneros com intervalo de confiança, faixas de preço, comparação multiplayer e cobertura de plataformas."),
            ("Opportunity explorer", "Apresenta o gráfico de oportunidades, tabela formatada e botão para baixar apenas as combinações filtradas."),
            ("Market evidence", "Mostra tags, correlações e tendência temporal. Inclui alertas para não interpretar tags retrospectivas como requisitos de produto."),
            ("Methodology", "Explica definição de sucesso, abordagem estatística e limitações. Também oferece download da base analítica limpa."),
        ])

        pagina_graficos_resultados(pdf, generos, precos, modos)

        tabela_combinacoes = combinacoes.head(8)[
            ["Genre", "price_band", "play_mode", "platform_count", "games", "success_rate", "lift_vs_baseline", "ci_low"]
        ].copy()
        pagina_tabela(
            pdf,
            "16. Principais combinações atuais",
            "Esta tabela é um exemplo do conteúdo consumido pelo explorador de oportunidades. A ordem utiliza evidence_score, não somente success_rate.",
            tabela_combinacoes,
            {
                "success_rate": lambda x: f"{x:.1%}",
                "lift_vs_baseline": lambda x: f"{x:.2f}x",
                "ci_low": lambda x: f"{x:.1%}",
            },
        )

        pagina_texto(pdf, "17. Como interpretar os resultados atuais", [
            ("Taxa-base", f"A referência para jogos pagos é {taxa_base:.2%}. Valores acima disso indicam associação positiva dentro do conjunto analisado."),
            ("Gênero", f"O RPG aparece no topo do ranking por evidência com taxa de {generos.iloc[0]['success_rate']:.2%} e lift de {generos.iloc[0]['lift_vs_baseline']:.2f}x."),
            ("Preço", f"A faixa {precos.iloc[0]['price_band']} aparece primeiro por evidência, com taxa de {precos.iloc[0]['success_rate']:.2%}. A faixa com maior taxa absoluta pode ser diferente porque tamanho e confiança também importam."),
            ("Multiplayer", f"Jogos com multiplayer possuem taxa observada de {modos.iloc[0]['success_rate']:.2%} e lift de {modos.iloc[0]['lift_vs_baseline']:.2f}x."),
            ("Decisão", "Os resultados servem para formular e priorizar hipóteses. Eles devem ser combinados com custo de produção, capacidade da equipe, validação de demanda, wishlists, marketing e análise de concorrentes."),
        ])

        pagina_texto(pdf, "18. Limitações técnicas e estatísticas", [
            ("Proprietários estimados", "São faixas amplas, não vendas exatas. O ponto médio simplifica uma incerteza real."),
            ("Preço observado", "O dataset pode refletir preço atual e descontos, não necessariamente preço de lançamento."),
            ("Variáveis ausentes", "Não existem custos de desenvolvimento, orçamento de marketing, reputação prévia, tamanho da equipe ou receita líquida."),
            ("Viés e causalidade", "A análise é observacional. Jogos bem-sucedidos podem receber ports e mais avaliações depois do sucesso. Portanto, associação não prova causa."),
            ("Tags", "Tags como Classic e Cult Classic descrevem percepção ou resultado retrospectivo. Não são funcionalidades que podem ser escolhidas diretamente."),
            ("Critérios ajustáveis", "Percentil 80, 20 avaliações, 75% positivo, preço máximo de US$ 100 e mínimo de 100 jogos são decisões explícitas. Alterá-las muda os resultados."),
        ])

        pagina_texto(pdf, "19. Como executar e revisar", [
            ("Requisitos", "Python com pandas, numpy, matplotlib e streamlit. O arquivo steam_dataset.csv deve estar no mesmo diretório dos scripts."),
            ("Passo 1", "Execute python steam_calculo.py. Confirme a criação de steam_analysis/ e dos CSVs. O console deve informar jogos limpos, jogos pagos e diretório de saída."),
            ("Passo 2", "Execute streamlit run steam_streamlit.py. O navegador abrirá o dashboard."),
            ("Passo 3", "Teste filtros individuais e combinações. Confirme que a tabela e a melhor oportunidade mudam. Use os botões de download."),
            ("Passo 4", "Revise metodologia e limitações antes de apresentar recomendações. Não trate taxas observadas como garantia de retorno."),
        ])

        pagina_texto(pdf, "20. Checklist de revisão de código", [
            ("steam_calculo.py", "Verificar se o reparo do cabeçalho continua válido para uma nova versão do dataset; confirmar datas e faixas de proprietários; revisar critérios de exclusão; validar definição de sucesso; comparar contagens antes e depois da limpeza; verificar duplicatas e ausências."),
            ("Estatísticas", "Confirmar taxa-base; inspecionar grupos pequenos; conferir intervalos de Wilson; revisar evidence_score; avaliar sensibilidade a critérios diferentes; evitar interpretação causal."),
            ("Streamlit", "Confirmar presença dos CSVs; testar cache; testar filtros vazios e sem resultados; verificar legibilidade dos gráficos; conferir downloads; revisar textos executivos quando os dados forem atualizados."),
            ("Operação", "Regenerar CSVs antes de abrir o dashboard após mudanças no pipeline. Manter os nomes de colunas persistidas porque o Streamlit depende desse contrato."),
        ])

        pagina_texto(pdf, "21. Glossário das principais colunas", [
            ("owners_midpoint", "Ponto médio entre os limites inferior e superior da faixa de proprietários estimados."),
            ("positive_ratio", "Avaliações positivas divididas pelo total de avaliações."),
            ("commercial_game", "Jogo pago com preço maior que zero e até US$ 100."),
            ("high_sales", "Jogo no percentil 80 ou superior de proprietários entre jogos pagos."),
            ("well_rated", "Jogo com pelo menos 20 avaliações e 75% positivas."),
            ("success", "Interseção de commercial_game, high_sales e well_rated."),
            ("success_rate", "Quantidade de sucessos dividida pela quantidade de jogos do grupo."),
            ("lift_vs_baseline", "Taxa do grupo dividida pela taxa-base dos jogos pagos."),
            ("ci_low / ci_high", "Limites inferior e superior do intervalo de confiança de Wilson."),
            ("evidence_score", "Pontuação de ordenação que combina limite inferior de confiança e tamanho da amostra."),
        ])

        pagina_texto(pdf, "Conclusão", [
            ("Separação correta", "steam_calculo.py é uma camada reproduzível de engenharia de dados e estatística. steam_streamlit.py é uma camada de apresentação, exploração e comunicação de negócio."),
            ("Força do projeto", "Os critérios estão explícitos, as saídas são persistidas, a incerteza é considerada por intervalos de confiança e grupos pequenos são controlados."),
            ("Próxima revisão recomendada", "Validar os critérios de sucesso com a realidade financeira da empresa. Se houver dados de orçamento, marketing e receita, incorporá-los para aproximar a análise de lucratividade, não apenas de alcance e avaliação."),
        ])

    print(f"PDF gerado: {SAIDA}")


if __name__ == "__main__":
    gerar()
