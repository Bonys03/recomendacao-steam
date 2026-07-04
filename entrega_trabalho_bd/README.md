# Trabalho Final BD - Adaptacao SQL e Elasticsearch

## Objetivo

Este projeto adapta o trabalho original de analise de oportunidades para jogos na Steam. A pergunta de negocio, os graficos, as features e a logica de analise continuam os mesmos. A mudanca esta na fonte dos dados:

- `app_sql.py`: le os dados de um banco relacional SQLite normalizado.
- `app_elastic.py`: le os dados de um indice Elasticsearch desnormalizado.

## Arquivos nesta entrega

Esta pasta contem apenas os arquivos essenciais de codigo, modelagem e documentacao do trabalho. Os artefatos grandes ou gerados ficaram fora do Git:

- `steam_dataset.csv`: dataset bruto baixado do Kaggle.
- `steam_analysis/`: saida gerada por `steam_calculo.py`.
- `steam_database.sqlite`: banco gerado por `criar_banco_steam.py`.

Esses arquivos podem ser recriados localmente pelos comandos abaixo.

## Como preparar o ambiente

```powershell
python -m pip install -r requirements.txt
python kaggle_collect
python steam_calculo.py
python criar_banco_steam.py
```

Depois disso, para carregar o Elasticsearch:

```powershell
python criar_banco_elasticsearch.py
```

## Modelagem SQL

Arquivo principal: `steam_schema.sql`

A tabela fato principal e `games`, onde cada linha representa um jogo limpo da base Steam. Os atributos multivalorados do CSV original foram normalizados em dimensoes e tabelas associativas.

Dimensoes:

- `developers`
- `publishers`
- `genres`
- `categories`
- `tags`
- `platforms`

Tabelas associativas com chave primaria composta:

- `game_developers`
- `game_publishers`
- `game_genres`
- `game_categories`
- `game_tags`
- `game_platforms`

A modelagem atende:

- 1FN: listas de generos, tags, categorias, plataformas, desenvolvedores e publicadoras foram separadas em linhas.
- 2FN: tabelas associativas usam chave composta e nao guardam atributos que dependem apenas de parte da chave.
- 3FN: nomes repetidos ficam nas dimensoes, nao diretamente na tabela `games`.

## Carga SQL

Arquivo: `criar_banco_steam.py`

Execucao:

```powershell
python criar_banco_steam.py
```

Saida:

- `steam_database.sqlite`

## Template Elasticsearch

Arquivo: `steam_elastic_template.json`

O Elasticsearch usa um modelo desnormalizado: cada documento representa um jogo completo, com arrays para `developers`, `publishers`, `genres`, `categories`, `tags` e `platforms`.

Decisoes principais de mapping:

- `name`: `text` com subcampo `keyword`, para busca textual e ordenacao/agregacao quando necessario.
- `genres`, `categories`, `tags`, `developers`, `publishers`, `platforms`: `keyword`, porque sao usados em filtros e agregacoes.
- `release_date`: `date`.
- metricas numericas como `price_usd`, `owners_midpoint`, `positive_ratio`: tipos numericos.

## Carga Elasticsearch

Arquivo: `criar_banco_elasticsearch.py`

Execucao local, com o Elasticsearch rodando:

```powershell
python criar_banco_elasticsearch.py
```

Com usuario e senha:

```powershell
$env:ELASTIC_USER='aluno'
$env:ELASTIC_PASSWORD='aluno123'
python criar_banco_elasticsearch.py
```

O script publica `steam_elastic_template.json`, cria o indice `steam_games` e indexa os jogos em lote.

## Apps Streamlit

Versao SQL:

```powershell
streamlit run app_sql.py
```

Versao Elasticsearch:

```powershell
streamlit run app_elastic.py
```

As duas versoes usam `steam_dashboard_core.py`, que concentra os mesmos calculos, graficos e layout. Assim, a comparacao entre SQL e Elasticsearch muda somente a origem dos dados, conforme solicitado no roteiro.
