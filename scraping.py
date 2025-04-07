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

#configuracao do selenium
def configurar_driver():
    options = Options()
    #options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    return driver

#analisa estrutura da pagina
def analisar_pagina(soup, nome_vereador=None):
    print(f"\n{'='*50}")
    print(f"ANÁLISE DA PÁGINA{' de ' + nome_vereador if nome_vereador else ''}")
    print(f"{'='*50}")
    
    tabelas = soup.find_all('table')
    print(f"Total de tabelas encontradas: {len(tabelas)}")
    
    for i, tabela in enumerate(tabelas):
        print(f"\nTabela {i+1}:")
        print(f"Classes: {tabela.get('class', 'Sem classes')}")
        
        thead = tabela.find('thead')
        if thead:
            colunas = [th.text.strip() for th in thead.find_all('th')]
            print(f"Colunas: {colunas}")
        else:
            print("Cabeçalho não encontrado")
        
        tbody = tabela.find('tbody')
        if tbody:
            linhas = tbody.find_all('tr')
            print(f"Número de linhas: {len(linhas)}")
            if linhas:
                primeira_linha = linhas[0]
                colunas = primeira_linha.find_all('td')
                if colunas:
                    valores = [col.text.strip() for col in colunas]
                    print(f"Exemplo de linha: {valores}")
        else:
            print("Corpo da tabela não encontrado")
    
    print(f"{'='*50}\n")

#converte texto para numero
def texto_para_numero(texto):
    if not texto or texto.strip() == '':
        return 0.0
    
    texto = re.sub(r'[R$\s]', '', texto)
    texto = texto.replace('.', '').replace(',', '.')
    
    try:
        return float(texto)
    except ValueError:
        print(f"Erro ao converter '{texto}' para número")
        return 0.0

#encontra tabela de gastos
def encontrar_tabela_gastos(soup):
    for tabela in soup.find_all('table'):
        thead = tabela.find('thead')
        if thead:
            cabecalhos = [th.text.strip() for th in thead.find_all('th')]
            cabecalhos_esperados = ["Especificação", "Credor", "CNPJ"]
            if all(cabecalho in cabecalhos for cabecalho in cabecalhos_esperados):
                return tabela
    
    tabela = soup.find('table', {'class': 'table table-striped'})
    if tabela:
        return tabela
    
    tabela = soup.find('table', {'class': 'table'})
    if tabela:
        return tabela
    
    tabelas = soup.find_all('table')
    if tabelas:
        tabela_mais_provavel = None
        max_linhas = 0
        
        for tabela in tabelas:
            tbody = tabela.find('tbody')
            if tbody:
                linhas = tbody.find_all('tr')
                if len(linhas) > max_linhas:
                    max_linhas = len(linhas)
                    tabela_mais_provavel = tabela
        
        return tabela_mais_provavel
    
    return None

#extrai gastos do vereador
def extrair_gastos_vereador(driver, ano, mes, nome_vereador, link):
    try:
        print(f"      Acessando link: {link}")
        driver.get(link)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        
        analisar_pagina(soup, nome_vereador)
        
        tabela = encontrar_tabela_gastos(soup)
        
        if not tabela:
            print(f"Tabela não encontrada para {nome_vereador}")
            return []
        
        dados_gastos = []
        
        tbody = tabela.find('tbody')
        if not tbody:
            print(f"Corpo da tabela não encontrado para {nome_vereador}")
            return []
        
        for linha in tbody.find_all('tr'):
            colunas = linha.find_all('td')
            
            if len(colunas) >= 5:
                try:
                    especificacao = colunas[0].text.strip()
                    credor = colunas[1].text.strip()
                    cnpj = colunas[2].text.strip()
                    
                    valor_total = texto_para_numero(colunas[3].text.strip())
                    saldo = texto_para_numero(colunas[4].text.strip())
                    
                    dados_gastos.append({
                        'Ano': ano,
                        'Mês': mes,
                        'Vereador': nome_vereador,
                        'Especificação': especificacao,
                        'Credor': credor,
                        'CNPJ': cnpj,
                        'Valor Total': valor_total,
                        'Saldo': saldo
                    })
                    
                except Exception as e:
                    print(f"Erro ao processar linha para {nome_vereador}: {str(e)}")
                    print(f"Conteúdo da linha: {[col.text.strip() for col in colunas]}")
        
        if not dados_gastos:
            print(f"Nenhum dado extraído para {nome_vereador}")
            
            print("Tentando extração manual...")
            
            linhas_selenium = driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
            if linhas_selenium:
                print(f"Encontradas {len(linhas_selenium)} linhas via Selenium")
                
                for linha in linhas_selenium:
                    try:
                        colunas = linha.find_elements(By.TAG_NAME, "td")
                        if len(colunas) >= 5:
                            especificacao = colunas[0].text.strip()
                            credor = colunas[1].text.strip()
                            cnpj = colunas[2].text.strip()
                            valor_total = texto_para_numero(colunas[3].text.strip())
                            saldo = texto_para_numero(colunas[4].text.strip())
                            
                            dados_gastos.append({
                                'Ano': ano,
                                'Mês': mes,
                                'Vereador': nome_vereador,
                                'Especificação': especificacao,
                                'Credor': credor,
                                'CNPJ': cnpj,
                                'Valor Total': valor_total,
                                'Saldo': saldo
                            })
                    except Exception as e:
                        print(f"Erro na extração manual: {str(e)}")
        
        print(f"      Extraídos {len(dados_gastos)} registros de gastos para {nome_vereador}")
        return dados_gastos
    
    except Exception as e:
        print(f"Erro ao extrair gastos de {nome_vereador}: {str(e)}")
        return []

#verifica numero de paginas
def verificar_numero_paginas(driver, ano, mes):
    url = f"https://portaltransparencia.cmfor.ce.gov.br/despesas/sdp?&page=1&ano={ano}&mes={mes}&nome="
    driver.get(url)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
    )
    
    try:
        paginacao = driver.find_element(By.CLASS_NAME, "pagination")
        links_paginas = paginacao.find_elements(By.TAG_NAME, "a")
        
        if links_paginas:
            numeros_paginas = []
            for link in links_paginas:
                texto = link.text.strip()
                if texto.isdigit():
                    numeros_paginas.append(int(texto))
            
            if numeros_paginas:
                return max(numeros_paginas)
        
        tabela = driver.find_element(By.TAG_NAME, "tbody")
        if tabela:
            linhas = tabela.find_elements(By.TAG_NAME, "tr")
            if linhas:
                return 1
    
    except Exception as e:
        print(f"Erro ao verificar número de páginas: {str(e)}")
    
    return 3

#extrai vereadores de uma pagina
def extrair_vereadores_pagina(driver, ano, mes, pagina):
    url = f"https://portaltransparencia.cmfor.ce.gov.br/despesas/sdp?&page={pagina}&ano={ano}&mes={mes}&nome="
    
    print(f"    Acessando URL: {url}")
    driver.get(url)
    
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "tbody"))
        )
        
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tabela = soup.find('tbody')
        
        if not tabela:
            print(f"    AVISO: Tabela não encontrada na página {pagina} do mês {mes}/{ano}")
            return [], []
        
        vereadores = []
        links = []
        
        for linha in tabela.find_all('tr'):
            colunas = linha.find_all('td')
            if len(colunas) >= 4:
                ano_vereador = colunas[0].text.strip()
                mes_vereador = colunas[1].text.strip()
                nome_vereador = colunas[2].text.strip()
                link_element = colunas[3].find('a')
                
                if link_element and 'href' in link_element.attrs:
                    link = "https://portaltransparencia.cmfor.ce.gov.br" + link_element['href']
                    vereadores.append(nome_vereador)
                    links.append(link)
        
        print(f"    Encontrados {len(vereadores)} vereadores na página {pagina}")
        return vereadores, links
    
    except Exception as e:
        print(f"    ERRO ao extrair vereadores da página {pagina}: {str(e)}")
        return [], []

#coleta dados dos vereadores
def coletar_dados_vereadores(meses, ano):
    driver = configurar_driver()
    
    todos_gastos = []
    
    try:
        for mes in meses:
            print(f"\nColetando dados de {mes}/{ano}...")
            
            try:
                num_paginas = verificar_numero_paginas(driver, ano, mes)
                print(f"  Detectadas {num_paginas} páginas para o mês {mes}/{ano}")
            except Exception as e:
                print(f"  Erro ao verificar número de páginas: {str(e)}")
                num_paginas = 3
                print(f"  Usando valor padrão: {num_paginas} páginas")
            
            gastos_mes = []
            
            for pagina in range(1, num_paginas + 1):
                print(f"\n  Processando página {pagina} de {num_paginas} para o mês {mes}/{ano}...")
                
                vereadores, links = extrair_vereadores_pagina(driver, ano, mes, pagina)
                
                if not vereadores:
                    print(f"  AVISO: Nenhum vereador encontrado na página {pagina} do mês {mes}/{ano}")
                    continue
                
                print(f"  Encontrados {len(vereadores)} vereadores na página {pagina}")
                
                for i, (vereador, link) in enumerate(zip(vereadores, links)):
                    print(f"    Processando vereador {i+1}/{len(vereadores)}: {vereador}")
                    gastos = extrair_gastos_vereador(driver, ano, mes, vereador, link)
                    gastos_mes.extend(gastos)
                    
                    time.sleep(1.5)
            
            print(f"  Total de {len(gastos_mes)} registros de gastos extraídos para o mês {mes}/{ano}")
            todos_gastos.extend(gastos_mes)
        
        df = pd.DataFrame(todos_gastos)
        
        if not os.path.exists('dados'):
            os.makedirs('dados')
        
        data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_arquivo = f"dados/gastos_vereadores_{ano}_{data_atual}.csv"
        df.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')
        
        print(f"\nDados salvos com sucesso em {caminho_arquivo}")
        print(f"Total de {len(todos_gastos)} registros extraídos para todos os meses")
        return caminho_arquivo
    
    finally:
        driver.quit()

#execucao principal
if __name__ == "__main__":
    meses_semestre = list(range(7, 13))
    ano = 2024
    
    caminho_arquivo = coletar_dados_vereadores(meses_semestre, ano)
    print(f"Webscraping concluído. Dados salvos em {caminho_arquivo}")