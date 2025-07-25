import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import glob
from datetime import datetime
import matplotlib.ticker as mtick
from typing import Optional, Tuple, List, Dict
from pathlib import Path

class VereadoresAnalyzer:
    def __init__(self):
        # Configurações iniciais de estilo e formatação
        self._setup_plot_style()
        self.output_dir = "graficos"
        self.ensure_directory_exists(self.output_dir)
        
    def _setup_plot_style(self) -> None:
        """Configura o estilo padrão para os gráficos."""
        pd.options.display.float_format = 'R$ {:.2f}'.format
        plt.style.use('ggplot')
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'DejaVu Sans'],
            'axes.unicode_minus': False,
            'figure.figsize': (12, 8)
        })
        sns.set_palette("colorblind")
    
    @staticmethod
    def ensure_directory_exists(dir_path: str) -> None:
        """Garante que o diretório especificado existe."""
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def _load_most_recent_file(self) -> Optional[pd.DataFrame]:
        """Carrega o arquivo de dados mais recente."""
        files = glob.glob('dados/gastos_vereadores_*.csv')
        
        if not files:
            print("Nenhum arquivo de dados encontrado. Execute primeiro o script de scraping.")
            return None
        
        most_recent_file = max(files, key=os.path.getmtime)
        print(f"Carregando dados do arquivo: {most_recent_file}")
        
        try:
            return pd.read_csv(most_recent_file, encoding='utf-8-sig')
        except Exception as e:
            print(f"Erro ao carregar arquivo: {str(e)}")
            return None
    
    @staticmethod
    def _format_currency(value: float, pos=None) -> str:
        """Formata valores em reais para exibição nos gráficos."""
        return f'R$ {value:,.0f}'
    
    def _generate_basic_stats(self, df: pd.DataFrame) -> None:
        """Gera estatísticas básicas sobre os dados."""
        print("\n=== ESTATÍSTICAS BÁSICAS ===")
        
        # Gastos por mês
        monthly_expenses = df.groupby('Mês')['Valor Total'].sum().reset_index()
        print("\nTotal de gastos por mês:")
        for _, row in monthly_expenses.iterrows():
            print(f"Mês {int(row['Mês'])}: R$ {row['Valor Total']:,.2f}")
        
        # Top 10 vereadores com maiores gastos
        top_vereadores = df.groupby('Vereador')['Valor Total'].sum().sort_values(ascending=False)
        print("\nTop 10 vereadores com maiores gastos:")
        for vereador, valor in list(top_vereadores.items())[:10]:
            print(f"{vereador}: R$ {valor:,.2f}")
        
        # Principais categorias de gastos
        top_categories = df.groupby('Especificação')['Valor Total'].sum().sort_values(ascending=False)
        print("\nPrincipais categorias de gastos:")
        for categoria, valor in list(top_categories.items())[:5]:
            print(f"{categoria}: R$ {valor:,.2f}")
        
        # Principais credores
        top_credores = df.groupby('Credor')['Valor Total'].sum().sort_values(ascending=False)
        print("\nPrincipais credores:")
        for credor, valor in list(top_credores.items())[:5]:
            print(f"{credor}: R$ {valor:,.2f}")
    
    def _save_plot(self, filename: str, dpi: int = 300) -> None:
        """Salva o gráfico atual no diretório de saída."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"{filename}_{timestamp}.png")
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi)
        plt.close()
        print(f"Gráfico salvo: {output_path}")
    
    def _plot_monthly_expenses(self, df: pd.DataFrame) -> None:
        """Gera gráfico de gastos por mês."""
        monthly_expenses = df.groupby('Mês')['Valor Total'].sum().reset_index()
        
        plt.figure(figsize=(12, 7))
        ax = sns.barplot(x='Mês', y='Valor Total', data=monthly_expenses, palette='viridis')
        
        plt.title('Total Gasto por Mês', fontsize=18)
        plt.xlabel('Mês', fontsize=14)
        plt.ylabel('Valor Total', fontsize=14)
        plt.xticks(rotation=0, fontsize=12)
        plt.yticks(fontsize=12)
        
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(self._format_currency))
        
        for i, bar in enumerate(ax.patches):
            valor = monthly_expenses.iloc[i]['Valor Total']
            ax.annotate(f'R$ {valor:,.0f}', 
                       (bar.get_x() + bar.get_width() / 2., bar.get_height()), 
                       ha='center', va='bottom', fontsize=11)
        
        self._save_plot("gastos_por_mes")
    
    def _plot_top_vereadores(self, df: pd.DataFrame, top_n: int = 15) -> None:
        """Gera gráfico de ranking de vereadores por gastos."""
        top_vereadores = df.groupby('Vereador')['Valor Total'].sum().nlargest(top_n).reset_index()
        
        plt.figure(figsize=(14, 10))
        ax = sns.barplot(x='Valor Total', y='Vereador', data=top_vereadores, palette='viridis')
        
        plt.title(f'Total por Vereador (Top {top_n})', fontsize=18)
        plt.xlabel('Valor Total', fontsize=14)
        plt.ylabel('Vereador', fontsize=14)
        plt.yticks(fontsize=12)
        plt.xticks(fontsize=12)
        
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(self._format_currency))
        
        for i, bar in enumerate(ax.patches):
            valor = top_vereadores.iloc[i]['Valor Total']
            ax.annotate(f'R$ {valor:,.0f}', 
                       (bar.get_width(), bar.get_y() + bar.get_height()/2), 
                       ha='left', va='center', fontsize=11)
        
        self._save_plot("total_por_vereador")
    
    def _plot_category_distribution(self, df: pd.DataFrame, top_n: int = 7) -> None:
        """Gera gráfico de distribuição por categoria."""
        top_categories = df.groupby('Especificação')['Valor Total'].sum().nlargest(top_n).reset_index()
        total = top_categories['Valor Total'].sum()
        top_categories['Porcentagem'] = (top_categories['Valor Total'] / total) * 100
        
        plt.figure(figsize=(14, 10))
        plt.pie(top_categories['Valor Total'], 
                labels=[f"{cat} (R$ {val:,.0f})" for cat, val in zip(top_categories['Especificação'], top_categories['Valor Total'])], 
                autopct='%1.1f%%', startangle=90, shadow=True,
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
        
        plt.axis('equal')
        plt.title(f'Distribuição de Gastos por Categoria (Top {top_n})', fontsize=18)
        
        self._save_plot("distribuicao_por_categoria")
    
    def _plot_top_credores(self, df: pd.DataFrame, top_n: int = 10) -> None:
        """Gera gráfico dos principais credores."""
        top_credores = df.groupby('Credor')['Valor Total'].sum().nlargest(top_n).reset_index()
        
        plt.figure(figsize=(14, 8))
        ax = sns.barplot(x='Valor Total', y='Credor', data=top_credores, palette='viridis')
        
        plt.title(f'Top {top_n} Credores', fontsize=18)
        plt.xlabel('Valor Total', fontsize=14)
        plt.ylabel('Credor', fontsize=14)
        plt.yticks(fontsize=12)
        plt.xticks(fontsize=12)
        
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(self._format_currency))
        
        for i, bar in enumerate(ax.patches):
            valor = top_credores.iloc[i]['Valor Total']
            ax.annotate(f'R$ {valor:,.0f}', 
                       (bar.get_width(), bar.get_y() + bar.get_height()/2), 
                       ha='left', va='center', fontsize=11)
        
        self._save_plot("top_credores")
    
    def _plot_expense_evolution(self, df: pd.DataFrame, top_n: int = 5) -> None:
        """Gera gráfico de evolução de gastos por vereador."""
        top_vereadores = df.groupby('Vereador')['Valor Total'].sum().nlargest(top_n).index
        df_top = df[df['Vereador'].isin(top_vereadores)]
        
        pivot_df = df_top.pivot_table(index='Mês', columns='Vereador', values='Valor Total', aggfunc='sum')
        
        plt.figure(figsize=(14, 8))
        ax = pivot_df.plot(marker='o', linewidth=2.5, markersize=8)
        
        plt.title(f'Evolução de Gastos por Vereador (Top {top_n})', fontsize=18)
        plt.xlabel('Mês', fontsize=14)
        plt.ylabel('Valor Total', fontsize=14)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(title='Vereador', loc='best', fontsize=12)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(self._format_currency))
        
        self._save_plot("evolucao_gastos")
    
    def _plot_expense_balance_correlation(self, df: pd.DataFrame) -> None:
        """Gera gráfico de correlação entre gastos e saldo."""
        correlation_df = df.groupby('Vereador').agg({
            'Valor Total': 'sum',
            'Saldo': 'mean'
        }).reset_index()
        
        plt.figure(figsize=(14, 8))
        ax = sns.scatterplot(data=correlation_df, x='Valor Total', y='Saldo', 
                         size='Valor Total', sizes=(100, 500), alpha=0.7)
        
        for i, row in correlation_df.iterrows():
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
        
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(self._format_currency))
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(self._format_currency))
        
        self._save_plot("correlacao_gastos_saldo")
    
    def _plot_heatmap(self, df: pd.DataFrame, top_n: int = 20) -> None:
        """Gera mapa de calor de gastos por vereador e mês."""
        top_vereadores = df.groupby('Vereador')['Valor Total'].sum().nlargest(top_n).index
        df_top = df[df['Vereador'].isin(top_vereadores)]
        
        heatmap_data = df_top.pivot_table(index='Vereador', columns='Mês', 
                                        values='Valor Total', aggfunc='sum', fill_value=0)
        
        heatmap_data = heatmap_data.reindex(
            df.groupby('Vereador')['Valor Total'].sum().nlargest(top_n).index
        )
        
        plt.figure(figsize=(16, 12))
        ax = sns.heatmap(heatmap_data, cmap='viridis', annot=True, fmt='.0f', 
                      linewidths=.5, cbar_kws={'label': 'Valor Total Gasto (R$)'})
        
        plt.title(f'Mapa de Calor: Gastos por Vereador e Mês (Top {top_n})', fontsize=18)
        plt.xlabel('Mês', fontsize=14)
        plt.ylabel('Vereador', fontsize=14)
        
        self._save_plot("mapa_calor")
    
    def generate_all_plots(self, df: pd.DataFrame) -> None:
        """Gera todos os gráficos de análise."""
        if df is None or df.empty:
            print("Sem dados para gerar gráficos.")
            return
        
        print("\nGerando gráficos de análise...")
        
        self._plot_monthly_expenses(df)
        self._plot_top_vereadores(df)
        self._plot_category_distribution(df)
        self._plot_top_credores(df)
        self._plot_expense_evolution(df)
        self._plot_expense_balance_correlation(df)
        self._plot_heatmap(df)
        
        print("\nTodos os gráficos foram gerados com sucesso!")
    
    def _detailed_analysis(self, df: pd.DataFrame) -> None:
        """Realiza análise detalhada dos dados."""
        print("\n=== ANÁLISE DETALHADA ===")
        
        # Média de gastos por vereador
        avg_per_vereador = df.groupby('Vereador')['Valor Total'].mean().sort_values(ascending=False)
        print("\nMédia de gastos por vereador (top 5):")
        for vereador, valor in list(avg_per_vereador.items())[:5]:
            print(f"{vereador}: R$ {valor:,.2f}")
        
        # Variação de gastos
        expense_variation = df.groupby('Vereador')['Valor Total'].agg(['sum', 'mean', 'std']).sort_values(by='sum', ascending=False)
        expense_variation['std'] = expense_variation['std'].fillna(0)
        
        print("\nVariação de gastos (top 5 por total de gastos):")
        for vereador, row in list(expense_variation.iterrows())[:5]:
            print(f"{vereador}:")
            print(f"  Total: R$ {row['sum']:,.2f}")
            print(f"  Média: R$ {row['mean']:,.2f}")
            print(f"  Desvio Padrão: R$ {row['std']:,.2f}")
        
        # Tipo de gasto mais comum por vereador
        top_vereadores = list(df.groupby('Vereador')['Valor Total'].sum().sort_values(ascending=False).head(10).index)
        
        print("\nTipo de gasto mais comum por vereador (top 10 vereadores):")
        for vereador in top_vereadores:
            df_vereador = df[df['Vereador'] == vereador]
            main_expense = df_vereador.groupby('Especificação')['Valor Total'].sum().sort_values(ascending=False).head(1)
            if not main_expense.empty:
                categoria = main_expense.index[0]
                valor = main_expense.values[0]
                print(f"{vereador}: {categoria} (R$ {valor:,.2f})")
        
        # Comparação de gastos entre os meses
        if len(df['Mês'].unique()) > 1:
            print("\nComparação de gastos entre os meses:")
            for vereador in top_vereadores:
                df_vereador = df[df['Vereador'] == vereador]
                if len(df_vereador['Mês'].unique()) > 1:
                    monthly_expenses = df_vereador.groupby('Mês')['Valor Total'].sum()
                    min_month = monthly_expenses.idxmin()
                    max_month = monthly_expenses.idxmax()
                    
                    print(f"{vereador}:")
                    print(f"  Mês com menor gasto: {int(min_month)} (R$ {monthly_expenses[min_month]:,.2f})")
                    print(f"  Mês com maior gasto: {int(max_month)} (R$ {monthly_expenses[max_month]:,.2f})")
                    print(f"  Variação: {((monthly_expenses[max_month] / monthly_expenses[min_month]) - 1) * 100:.2f}%")
    
    def _print_data_summary(self, df: pd.DataFrame) -> None:
        """Exibe um resumo dos dados carregados."""
        print("\nInformações do DataFrame:")
        print(f"Colunas: {', '.join(df.columns)}")
        print(f"Período: Meses {df['Mês'].min()} a {df['Mês'].max()} de {df['Ano'].iloc[0]}")
        print(f"Total de vereadores: {df['Vereador'].nunique()}")
        print(f"Total de categorias de gastos: {df['Especificação'].nunique()}")
        print(f"Total de credores: {df['Credor'].nunique()}")
        print(f"Valor total dos gastos: R$ {df['Valor Total'].sum():,.2f}")
    
    def run_analysis(self) -> None:
        """Executa todo o fluxo de análise."""
        print("=== ANÁLISE DE GASTOS DOS VEREADORES DE FORTALEZA ===")
        
        df = self._load_most_recent_file()
        
        if df is not None:
            print(f"\nDados carregados com sucesso: {len(df)} registros")
            
            self._print_data_summary(df)
            self._generate_basic_stats(df)
            self._detailed_analysis(df)
            self.generate_all_plots(df)
            
            print("\nAnálise concluída!")

if __name__ == "__main__":
    analyzer = VereadoresAnalyzer()
    analyzer.run_analysis()
