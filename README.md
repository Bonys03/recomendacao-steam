# Recomendação de posicionamento para jogos na Steam

Projeto de engenharia e análise de dados que identifica características associadas ao sucesso comercial de jogos pagos na Steam. O resultado é apresentado em um dashboard interativo desenvolvido com Streamlit e Matplotlib.

## Problema de negócio

Quais combinações de gênero, faixa de preço, modo de jogo e cobertura de plataformas apresentam evidências históricas mais fortes de sucesso comercial na Steam?

O dashboard apoia a priorização de hipóteses para novos jogos. Os resultados são observacionais e não representam garantia de vendas.

## Definição de sucesso

Um jogo é classificado como bem-sucedido quando:

- É pago e custa no máximo US$ 100.
- Está entre os 20% dos jogos pagos com mais proprietários estimados.
- Possui pelo menos 20 avaliações.
- Possui pelo menos 75% de avaliações positivas.

Na base atual, o corte dos 20% superiores corresponde a pelo menos 35 mil proprietários estimados.

## Tratamento e engenharia de dados

O pipeline utiliza Pandas e NumPy para:

- Reparar o deslocamento das colunas do CSV original.
- Converter datas e campos numéricos inválidos.
- Interpretar faixas de proprietários e calcular seu ponto médio.
- Remover registros sem data, gênero ou proprietários estimados.
- Remover duplicatas, demos, trilhas sonoras, servidores e outros itens que não representam jogos completos.
- Criar quantidade de avaliações, proporção positiva, faixa de preço, ano, modo de jogo e quantidade de plataformas.
- Calcular taxa-base, ganho sobre a taxa-base, intervalo de confiança de Wilson e pontuação de evidência.
- Comparar combinações com pelo menos 100 jogos.

## Principais resultados

- 106.244 jogos permaneceram após a limpeza.
- 89.000 jogos pagos foram analisados.
- A taxa-base observada de sucesso foi 9,9%.
- Jogos multijogador, RPG e a faixa de US$ 10-20 apresentaram sinais históricos acima da média.
- A recomendação executiva é validar um conceito de RPG ou estratégia multijogador, com preço entre US$ 10 e US$ 20, começando pelo Windows.

## Estrutura

- `steam_dataset.csv`: dataset bruto armazenado com Git LFS.
- `steam_calculo.py`: limpeza, engenharia de features e geração das tabelas analíticas.
- `steam_streamlit.py`: dashboard interativo.
- `gerar_documentacao_pdf.py`: geração reproduzível do relatório auxiliar.
- `documentacao_tecnica_steam.pdf`: relatório com escopo, metodologia, resultados e conclusões.

## Como executar

Requisitos: Python 3.10 ou superior e Git LFS.

```powershell
git lfs install
git clone https://github.com/Bonys03/recomendacao-steam.git
cd recomendacao-steam
python -m pip install -r requirements.txt
python steam_calculo.py
streamlit run steam_streamlit.py
```

O pipeline cria o diretório `steam_analysis/` com os CSVs consumidos pelo Streamlit.

## Metodologia estatística

- Proprietários estimados são representados pelo ponto médio da faixa disponível.
- Intervalos de confiança de Wilson de 95% expressam a incerteza das taxas.
- A pontuação de evidência combina o limite inferior do intervalo com o tamanho da amostra.
- A correlação de Spearman mede associação monotônica, não causalidade.

## Limitações

- O dataset não informa custo de desenvolvimento nem investimento em marketing.
- Preços atuais podem diferir dos preços de lançamento.
- Cobertura de plataformas pode ser consequência do sucesso.
- Características associadas ao sucesso não necessariamente causam sucesso.
