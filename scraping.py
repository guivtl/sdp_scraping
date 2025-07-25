from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from datetime import datetime
import re
from typing import List, Dict, Tuple, Optional, Union

class WebScraperVereadores:
    def __init__(self):
        self.driver = self._configure_driver()
        self.wait_timeout = 10
        self.delay_between_requests = 1.5
        
    def _configure_driver(self) -> webdriver.Chrome:
        """Configura e retorna uma instância do WebDriver do Chrome."""
        options = Options()
        # options.add_argument("--headless")  # Descomente para modo headless
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        return webdriver.Chrome(options=options)
    
    def _analyze_page_structure(self, soup: BeautifulSoup, vereador_name: str = None) -> None:
        """Analisa e exibe a estrutura da página para fins de depuração."""
        separator = "=" * 50
        title = f"ANÁLISE DA PÁGINA{' de ' + vereador_name if vereador_name else ''}"
        
        print(f"\n{separator}\n{title}\n{separator}")
        
        tables = soup.find_all('table')
        print(f"Total de tabelas encontradas: {len(tables)}")
        
        for i, table in enumerate(tables, 1):
            print(f"\nTabela {i}:")
            print(f"Classes: {table.get('class', 'Sem classes')}")
            
            if thead := table.find('thead'):
                headers = [th.text.strip() for th in thead.find_all('th')]
                print(f"Cabeçalhos: {headers}")
            else:
                print("Cabeçalho não encontrado")
            
            if tbody := table.find('tbody'):
                rows = tbody.find_all('tr')
                print(f"Número de linhas: {len(rows)}")
                if rows:
                    first_row = rows[0]
                    cols = first_row.find_all('td')
                    if cols:
                        values = [col.text.strip() for col in cols]
                        print(f"Exemplo de linha: {values}")
            else:
                print("Corpo da tabela não encontrado")
        
        print(f"{separator}\n")
    
    def _convert_text_to_number(self, text: str) -> float:
        """Converte texto formatado como moeda para número float."""
        if not text or not text.strip():
            return 0.0
        
        cleaned_text = re.sub(r'[R$\s]', '', text)
        cleaned_text = cleaned_text.replace('.', '').replace(',', '.')
        
        try:
            return float(cleaned_text)
        except ValueError:
            print(f"Erro ao converter '{text}' para número")
            return 0.0
    
    def _find_expenses_table(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Encontra a tabela de gastos na página."""
        # Primeiro tenta encontrar por cabeçalhos específicos
        for table in soup.find_all('table'):
            if thead := table.find('thead'):
                headers = [th.text.strip() for th in thead.find_all('th')]
                required_headers = ["Especificação", "Credor", "CNPJ"]
                if all(req_header in headers for req_header in required_headers):
                    return table
        
        # Tenta encontrar por classes específicas
        for class_name in ['table table-striped', 'table']:
            if table := soup.find('table', {'class': class_name}):
                return table
        
        # Fallback: seleciona a tabela com mais linhas
        tables = soup.find_all('table')
        if tables:
            return max(tables, key=lambda t: len(t.find('tbody').find_all('tr')) if t.find('tbody') else 0)
        
        return None
    
    def _extract_vereador_expenses(self, url: str, year: int, month: int, vereador_name: str) -> List[Dict]:
        """Extrai os gastos de um vereador específico."""
        print(f"      Acessando link: {url}")
        self.driver.get(url)
        
        try:
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            self._analyze_page_structure(soup, vereador_name)
            
            if not (table := self._find_expenses_table(soup)):
                print(f"Tabela não encontrada para {vereador_name}")
                return []
            
            expenses_data = []
            
            if not (tbody := table.find('tbody')):
                print(f"Corpo da tabela não encontrado para {vereador_name}")
                return []
            
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                
                if len(cols) >= 5:
                    try:
                        expenses_data.append({
                            'Ano': year,
                            'Mês': month,
                            'Vereador': vereador_name,
                            'Especificação': cols[0].text.strip(),
                            'Credor': cols[1].text.strip(),
                            'CNPJ': cols[2].text.strip(),
                            'Valor Total': self._convert_text_to_number(cols[3].text.strip()),
                            'Saldo': self._convert_text_to_number(cols[4].text.strip())
                        })
                    except Exception as e:
                        print(f"Erro ao processar linha para {vereador_name}: {str(e)}")
                        print(f"Conteúdo da linha: {[col.text.strip() for col in cols]}")
            
            if not expenses_data:
                print(f"Nenhum dado extraído para {vereador_name}")
                print("Tentando extração manual via Selenium...")
                expenses_data = self._manual_extraction(year, month, vereador_name)
            
            print(f"      Extraídos {len(expenses_data)} registros de gastos para {vereador_name}")
            return expenses_data
        
        except Exception as e:
            print(f"Erro ao extrair gastos de {vereador_name}: {str(e)}")
            return []
    
    def _manual_extraction(self, year: int, month: int, vereador_name: str) -> List[Dict]:
        """Tentativa de extração manual quando a abordagem padrão falha."""
        expenses_data = []
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
        
        if rows:
            print(f"Encontradas {len(rows)} linhas via Selenium")
            
            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 5:
                        expenses_data.append({
                            'Ano': year,
                            'Mês': month,
                            'Vereador': vereador_name,
                            'Especificação': cols[0].text.strip(),
                            'Credor': cols[1].text.strip(),
                            'CNPJ': cols[2].text.strip(),
                            'Valor Total': self._convert_text_to_number(cols[3].text.strip()),
                            'Saldo': self._convert_text_to_number(cols[4].text.strip())
                        })
                except Exception as e:
                    print(f"Erro na extração manual: {str(e)}")
        
        return expenses_data
    
    def _get_number_of_pages(self, year: int, month: int) -> int:
        """Determina o número de páginas de resultados para o ano/mês."""
        url = f"https://portaltransparencia.cmfor.ce.gov.br/despesas/sdp?&page=1&ano={year}&mes={month}&nome="
        self.driver.get(url)
        
        WebDriverWait(self.driver, self.wait_timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
        )
        
        try:
            pagination = self.driver.find_element(By.CLASS_NAME, "pagination")
            page_links = pagination.find_elements(By.TAG_NAME, "a")
            
            if page_links:
                page_numbers = [int(link.text.strip()) for link in page_links if link.text.strip().isdigit()]
                if page_numbers:
                    return max(page_numbers)
            
            if self.driver.find_element(By.TAG_NAME, "tbody"):
                return 1
        
        except Exception as e:
            print(f"Erro ao verificar número de páginas: {str(e)}")
        
        return 3  # Fallback padrão
    
    def _extract_vereadores_from_page(self, year: int, month: int, page: int) -> Tuple[List[str], List[str]]:
        """Extrai lista de vereadores e links de uma página específica."""
        url = f"https://portaltransparencia.cmfor.ce.gov.br/despesas/sdp?&page={page}&ano={year}&mes={month}&nome="
        print(f"    Acessando URL: {url}")
        self.driver.get(url)
        
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "tbody"))
            )
            
            time.sleep(2)  # Espera adicional para carregamento
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            if not (table := soup.find('tbody')):
                print(f"    AVISO: Tabela não encontrada na página {page} do mês {month}/{year}")
                return [], []
            
            vereadores = []
            links = []
            
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 4:
                    name = cols[2].text.strip()
                    if link := cols[3].find('a', href=True):
                        full_link = "https://portaltransparencia.cmfor.ce.gov.br" + link['href']
                        vereadores.append(name)
                        links.append(full_link)
            
            print(f"    Encontrados {len(vereadores)} vereadores na página {page}")
            return vereadores, links
        
        except Exception as e:
            print(f"    ERRO ao extrair vereadores da página {page}: {str(e)}")
            return [], []
    
    def collect_data(self, months: List[int], year: int) -> str:
        """Coleta dados de gastos dos vereadores para os meses e ano especificados."""
        all_expenses = []
        
        try:
            for month in months:
                print(f"\nColetando dados de {month}/{year}...")
                
                try:
                    num_pages = self._get_number_of_pages(year, month)
                    print(f"  Detectadas {num_pages} páginas para o mês {month}/{year}")
                except Exception as e:
                    print(f"  Erro ao verificar número de páginas: {str(e)}")
                    num_pages = 3
                    print(f"  Usando valor padrão: {num_pages} páginas")
                
                month_expenses = []
                
                for page in range(1, num_pages + 1):
                    print(f"\n  Processando página {page} de {num_pages} para o mês {month}/{year}...")
                    
                    vereadores, links = self._extract_vereadores_from_page(year, month, page)
                    
                    if not vereadores:
                        print(f"  AVISO: Nenhum vereador encontrado na página {page} do mês {month}/{year}")
                        continue
                    
                    print(f"  Encontrados {len(vereadores)} vereadores na página {page}")
                    
                    for i, (vereador, link) in enumerate(zip(vereadores, links), 1):
                        print(f"    Processando vereador {i}/{len(vereadores)}: {vereador}")
                        expenses = self._extract_vereador_expenses(link, year, month, vereador)
                        month_expenses.extend(expenses)
                        
                        time.sleep(self.delay_between_requests)
                
                print(f"  Total de {len(month_expenses)} registros de gastos extraídos para o mês {month}/{year}")
                all_expenses.extend(month_expenses)
            
            df = pd.DataFrame(all_expenses)
            
            os.makedirs('dados', exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"dados/gastos_vereadores_{year}_{timestamp}.csv"
            
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            print(f"\nDados salvos com sucesso em {file_path}")
            print(f"Total de {len(all_expenses)} registros extraídos para todos os meses")
            return file_path
        
        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = WebScraperVereadores()
    months_range = list(range(7, 13))  # Julho a Dezembro
    year = 2024
    
    output_file = scraper.collect_data(months_range, year)
    print(f"Webscraping concluído. Dados salvos em {output_file}")
