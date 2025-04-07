import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import glob
from datetime import datetime
import matplotlib.ticker as mtick

#formatacao de numeros
pd.options.display.float_format = 'R$ {:.2f}'.format
plt.style.use('ggplot')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

#carrega arquivo mais recente
def carregar_dados():
    arquivos = glob.glob('dados/gastos_vereadores_*.csv')
    
    if not arquivos:
        print("Nenhum arquivo de dados encontrado. Execute primeiro o script de scraping.")
        return None
    
    arquivo_mais_recente = max(arquivos, key=os.path.getmtime)
    print(f"Carregando dados do arquivo: {arquivo_mais_recente}")
    
    df = pd.read_csv(arquivo_mais_recente, encoding='utf-8-sig')
    return df

#formata valores em reais
def formatar_valor_reais(x, pos):
    return f'R$ {x:,.0f}'

#gera estatisticas basicas
def gerar_estatisticas_basicas(df):
    if df is None or df.empty:
        print("Sem dados para análise.")
        return
    
    print("\n=== ESTATÍSTICAS BÁSICAS ===")
    
    gastos_por_mes = df.groupby('Mês')['Valor Total'].sum().reset_index()
    print("\nTotal de gastos por mês:")
    for _, row in gastos_por_mes.iterrows():
        print(f"Mês {int(row['Mês'])}: R$ {row['Valor Total']:,.2f}")
    
    gastos_por_vereador = df.groupby('Vereador')['Valor Total'].sum().sort_values(ascending=False)
    print("\nTop 10 vereadores com maiores gastos:")
    for vereador, valor in list(gastos_por_vereador.items())[:10]:
        print(f"{vereador}: R$ {valor:,.2f}")
    
    gastos_por_categoria = df.groupby('Especificação')['Valor Total'].sum().sort_values(ascending=False)
    print("\nPrincipais categorias de gastos:")
    for categoria, valor in list(gastos_por_categoria.items())[:5]:
        print(f"{categoria}: R$ {valor:,.2f}")
    
    gastos_por_credor = df.groupby('Credor')['Valor Total'].sum().sort_values(ascending=False)
    print("\nPrincipais credores:")
    for credor, valor in list(gastos_por_credor.items())[:5]:
        print(f"{credor}: R$ {valor:,.2f}")

#gera graficos de analise
def gerar_graficos(df):
    if df is None or df.empty:
        print("Sem dados para gerar gráficos.")
        return
    
    if not os.path.exists('graficos'):
        os.makedirs('graficos')
    
    data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.style.use('ggplot')
    sns.set_palette("colorblind")
    
    formato_real = mtick.FuncFormatter(formatar_valor_reais)
    
    #grafico de gastos por mes
    plt.figure(figsize=(12, 7))
    gastos_por_mes = df.groupby('Mês')['Valor Total'].sum().reset_index()
    ax = sns.barplot(x='Mês', y='Valor Total', data=gastos_por_mes, palette='viridis')
    plt.title('Total Gasto por Mês', fontsize=18)
    plt.xlabel('Mês', fontsize=14)
    plt.ylabel('Valor Total', fontsize=14)
    plt.xticks(rotation=0, fontsize=12)
    plt.yticks(fontsize=12)
    ax.yaxis.set_major_formatter(formato_real)
    for i, p in enumerate(ax.patches):
        valor = gastos_por_mes.iloc[i]['Valor Total']
        ax.annotate(f'R$ {valor:,.0f}', 
                   (p.get_x() + p.get_width() / 2., p.get_height()), 
                   ha = 'center', va = 'bottom', fontsize=11)
    plt.tight_layout()
    plt.savefig(f'graficos/gastos_por_mes_{data_atual}.png', dpi=300)
    plt.close()
    
    #ranking de vereadores
    plt.figure(figsize=(14, 10))
    top_vereadores = df.groupby('Vereador')['Valor Total'].sum().nlargest(15).reset_index()
    ax = sns.barplot(x='Valor Total', y='Vereador', data=top_vereadores, palette='viridis')
    plt.title('Total por Vereador (Top 15)', fontsize=18)
    plt.xlabel('Valor Total', fontsize=14)
    plt.ylabel('Vereador', fontsize=14)
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=12)
    ax.xaxis.set_major_formatter(formato_real)
    for i, p in enumerate(ax.patches):
        valor = top_vereadores.iloc[i]['Valor Total']
        ax.annotate(f'R$ {valor:,.0f}', 
                   (p.get_width(), p.get_y() + p.get_height()/2), 
                   ha = 'left', va = 'center', fontsize=11)
    plt.tight_layout()
    plt.savefig(f'graficos/total_por_vereador_{data_atual}.png', dpi=300)
    plt.close()
    
    #distribuicao por categoria
    plt.figure(figsize=(14, 10))
    top_categorias = df.groupby('Especificação')['Valor Total'].sum().nlargest(7).reset_index()
    total = top_categorias['Valor Total'].sum()
    top_categorias['Porcentagem'] = (top_categorias['Valor Total'] / total) * 100
    
    plt.pie(top_categorias['Valor Total'], 
            labels=[f"{cat} (R$ {val:,.0f})" for cat, val in zip(top_categorias['Especificação'], top_categorias['Valor Total'])], 
            autopct='%1.1f%%', startangle=90, shadow=True,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
    plt.axis('equal')
    plt.title('Distribuição de Gastos por Categoria (Top 7)', fontsize=18)
    plt.tight_layout()
    plt.savefig(f'graficos/distribuicao_por_categoria_{data_atual}.png', dpi=300)
    plt.close()
    
    #principais credores
    plt.figure(figsize=(14, 8))
    top_credores = df.groupby('Credor')['Valor Total'].sum().nlargest(10).reset_index()
    ax = sns.barplot(x='Valor Total', y='Credor', data=top_credores, palette='viridis')
    plt.title('Top 10 Credores', fontsize=18)
    plt.xlabel('Valor Total', fontsize=14)
    plt.ylabel('Credor', fontsize=14)
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=12)
    ax.xaxis.set_major_formatter(formato_real)
    for i, p in enumerate(ax.patches):
        valor = top_credores.iloc[i]['Valor Total']
        ax.annotate(f'R$ {valor:,.0f}', 
                   (p.get_width(), p.get_y() + p.get_height()/2), 
                   ha = 'left', va = 'center', fontsize=11)
    plt.tight_layout()
    plt.savefig(f'graficos/top_credores_{data_atual}.png', dpi=300)
    plt.close()
    
    #evolucao de gastos
    plt.figure(figsize=(14, 8))
    top5_vereadores = df.groupby('Vereador')['Valor Total'].sum().nlargest(5).index
    df_top5 = df[df['Vereador'].isin(top5_vereadores)]
    
    pivot_df = df_top5.pivot_table(index='Mês', columns='Vereador', values='Valor Total', aggfunc='sum')
    
    ax = pivot_df.plot(marker='o', linewidth=2.5, markersize=8)
    
    plt.title('Evolução de Gastos por Vereador (Top 5)', fontsize=18)
    plt.xlabel('Mês', fontsize=14)
    plt.ylabel('Valor Total', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title='Vereador', loc='best', fontsize=12)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    ax.yaxis.set_major_formatter(formato_real)
    plt.tight_layout()
    plt.savefig(f'graficos/evolucao_gastos_{data_atual}.png', dpi=300)
    plt.close()
    
    #correlacao gastos e saldo
    plt.figure(figsize=(14, 8))
    correlacao_df = df.groupby('Vereador').agg({
        'Valor Total': 'sum',
        'Saldo': 'mean'
    }).reset_index()
    
    plt.figure(figsize=(14, 8))
    ax = sns.scatterplot(data=correlacao_df, x='Valor Total', y='Saldo', 
                     size='Valor Total', sizes=(100, 500), alpha=0.7)
    
    for i, row in correlacao_df.iterrows():
        plt.annotate(row['Vereador'], 
                    (row['Valor Total'], row['Saldo']),
                    xytext=(7, 0), 
                    textcoords='offset points',
                    fontsize=9)
    
    plt.title('Correlação entre Gastos e Saldo Médio por Vereador', fontsize=18)
    plt.xlabel('Valor Total Gasto', fontsize=14)
    plt.ylabel('Saldo Médio', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    ax.xaxis.set_major_formatter(formato_real)
    ax.yaxis.set_major_formatter(formato_real)
    plt.tight_layout()
    plt.savefig(f'graficos/correlacao_gastos_saldo_{data_atual}.png', dpi=300)
    plt.close()
    
    #mapa de calor
    plt.figure(figsize=(16, 12))
    
    top20_vereadores = df.groupby('Vereador')['Valor Total'].sum().nlargest(20).index
    df_top20 = df[df['Vereador'].isin(top20_vereadores)]
    
    heatmap_data = df_top20.pivot_table(index='Vereador', columns='Mês', 
                                      values='Valor Total', aggfunc='sum', fill_value=0)
    
    heatmap_data = heatmap_data.reindex(df.groupby('Vereador')['Valor Total'].sum().nlargest(20).index)
    
    ax = sns.heatmap(heatmap_data, cmap='viridis', annot=True, fmt='.0f', 
                  linewidths=.5, cbar_kws={'label': 'Valor Total Gasto (R$)'})
    
    plt.title('Mapa de Calor: Gastos por Vereador e Mês', fontsize=18)
    plt.xlabel('Mês', fontsize=14)
    plt.ylabel('Vereador', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'graficos/mapa_calor_{data_atual}.png', dpi=300)
    plt.close()
    
    print(f"\nGráficos salvos na pasta 'graficos' com o timestamp {data_atual}")

#analise detalhada dos dados
def analise_detalhada(df):
    if df is None or df.empty:
        print("Sem dados para análise detalhada.")
        return
    
    print("\n=== ANÁLISE DETALHADA ===")
    
    media_por_vereador = df.groupby('Vereador')['Valor Total'].mean().sort_values(ascending=False)
    print("\nMédia de gastos por vereador (top 5):")
    for vereador, valor in list(media_por_vereador.items())[:5]:
        print(f"{vereador}: R$ {valor:,.2f}")
    
    variacao_gastos = df.groupby('Vereador')['Valor Total'].agg(['sum', 'mean', 'std']).sort_values(by='sum', ascending=False)
    variacao_gastos['std'] = variacao_gastos['std'].fillna(0)
    
    print("\nVariação de gastos (top 5 por total de gastos):")
    for vereador, row in list(variacao_gastos.iterrows())[:5]:
        print(f"{vereador}:")
        print(f"  Total: R$ {row['sum']:,.2f}")
        print(f"  Média: R$ {row['mean']:,.2f}")
        print(f"  Desvio Padrão: R$ {row['std']:,.2f}")
    
    print("\nTipo de gasto mais comum por vereador (top 10 vereadores):")
    top10_vereadores = list(df.groupby('Vereador')['Valor Total'].sum().sort_values(ascending=False).head(10).index)
    
    for vereador in top10_vereadores:
        df_vereador = df[df['Vereador'] == vereador]
        gasto_principal = df_vereador.groupby('Especificação')['Valor Total'].sum().sort_values(ascending=False).head(1)
        if not gasto_principal.empty:
            categoria = gasto_principal.index[0]
            valor = gasto_principal.values[0]
            print(f"{vereador}: {categoria} (R$ {valor:,.2f})")
    
    if len(df['Mês'].unique()) > 1:
        print("\nComparação de gastos entre os meses:")
        for vereador in top10_vereadores:
            df_vereador = df[df['Vereador'] == vereador]
            if len(df_vereador['Mês'].unique()) > 1:
                gastos_mensais = df_vereador.groupby('Mês')['Valor Total'].sum()
                mes_min = gastos_mensais.idxmin()
                mes_max = gastos_mensais.idxmax()
                
                print(f"{vereador}:")
                print(f"  Mês com menor gasto: {int(mes_min)} (R$ {gastos_mensais[mes_min]:,.2f})")
                print(f"  Mês com maior gasto: {int(mes_max)} (R$ {gastos_mensais[mes_max]:,.2f})")
                print(f"  Variação: {((gastos_mensais[mes_max] / gastos_mensais[mes_min]) - 1) * 100:.2f}%")

#funcao principal
def main():
    print("=== ANÁLISE DE GASTOS DOS VEREADORES DE FORTALEZA ===")
    
    df = carregar_dados()
    
    if df is not None:
        print(f"\nDados carregados com sucesso: {len(df)} registros")
        
        print("\nInformações do DataFrame:")
        print(f"Colunas: {', '.join(df.columns)}")
        print(f"Período: Meses {df['Mês'].min()} a {df['Mês'].max()} de {df['Ano'].iloc[0]}")
        print(f"Total de vereadores: {df['Vereador'].nunique()}")
        print(f"Total de categorias de gastos: {df['Especificação'].nunique()}")
        print(f"Total de credores: {df['Credor'].nunique()}")
        print(f"Valor total dos gastos: R$ {df['Valor Total'].sum():,.2f}")
        
        gerar_estatisticas_basicas(df)
        
        analise_detalhada(df)
        
        gerar_graficos(df)
        
        print("\nAnálise concluída!")
    
if __name__ == "__main__":
    main() 