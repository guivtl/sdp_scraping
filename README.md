# Análise de Gastos dos Vereadores de Fortaleza

Este projeto coleta e analisa dados de gastos dos vereadores da Câmara Municipal de Fortaleza através do portal de transparência.

## O que faz

O projeto tem duas partes principais:

**scraping.py** - Coleta automaticamente os dados de gastos do portal de transparência da Câmara de Fortaleza. Navega pelas páginas e extrai informações sobre especificação dos gastos, credores, valores e saldos de cada vereador.

**analise.py** - Analisa os dados coletados e gera gráficos mostrando gastos por mês, ranking de vereadores, principais categorias de gastos, credores mais frequentes e outras visualizações.

## Como usar

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute a coleta de dados:
```bash
python scraping.py
```

3. Gere as análises:
```bash
python analise.py
```

Os dados ficam salvos na pasta `dados/` e os gráficos na pasta `graficos/`.

## Dados analisados

O projeto analisa gastos de julho a dezembro de 2024, incluindo informações sobre especificação dos gastos, credores, valores totais e saldos de cada vereador.

## Dependências

beautifulsoup4, matplotlib, numpy, pandas, selenium, seaborn 