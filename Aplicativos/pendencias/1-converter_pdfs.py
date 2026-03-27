if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass
import pdfplumber
import pandas as pd
import re
from collections import defaultdict
from pathlib import Path
import subprocess
import sys



def parse_pdfs():
    # Regex para a linha de detalhe do produto
    pattern = re.compile(r"^(\d+)\s+([\s\S]+?)\s+(\d+)\s+(\d{2}/\d{2}/\d{4})\s+[A-Za-z]+\s+(\d+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)$")
    
    # Regex para capturar a loja (a "linha cinza")
    # Exemplo: 1 SUPERMERCADO BAKLIZI LTDA 001-BAKLIZI
    loja_pattern = re.compile(r"^\d+\s+.+?\s+(\d{3})-[A-Za-z0-9]+$")

    base_dir = Path(__file__).parent
    pasta_entrada = base_dir / "bd_entrada"
    pasta_saida = base_dir / "bd_saida"
    
    pasta_entrada.mkdir(exist_ok=True)
    pasta_saida.mkdir(exist_ok=True)
    
    # Limpar arquivos Excel antigos da pasta de saída
    arquivos_antigos = pasta_saida.glob("*.xlsx")
    for arquivo in arquivos_antigos:
        try:
            arquivo.unlink()
        except OSError:
            pass

    pdf_files = list(pasta_entrada.glob("*.pdf"))
    
    if not pdf_files:
        print("Nenhum arquivo PDF encontrado na pasta bd_entrada.")
        return
    
    # Dicionário para armazenar dados de cada loja encontrados em todos os PDFs
    lojas_data = defaultdict(list)

    for pdf_path in pdf_files:
        print(f"Processando {pdf_path.name}...")
        
        current_loja = "000"  # Padrão caso os dados comecem antes de achar uma loja
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                for line in lines:
                    line_strip = line.strip()
                    
                    # Tenta dar match na identificação de loja ("linha cinza")
                    match_loja = loja_pattern.match(line_strip)
                    if match_loja:
                        current_loja = match_loja.group(1)
                        continue
                        
                    # Tenta dar match na linha de produto
                    match_produto = pattern.match(line_strip)
                    if match_produto:
                        codigo = match_produto.group(1)
                        produto = match_produto.group(2)
                        pedido = match_produto.group(3)
                        data = match_produto.group(4)
                        embal = int(match_produto.group(5))
                        
                        deposito_str = match_produto.group(7)
                        qtde_str = match_produto.group(8)
                        
                        # Convert "2.201,50" -> 2201.50 -> 2201
                        deposito = int(float(deposito_str.replace('.', '').replace(',', '.')))
                        qtde = int(float(qtde_str.replace('.', '').replace(',', '.')))
                        
                        lojas_data[current_loja].append({
                            "Codigo": codigo,
                            "Produto": produto,
                            "Nro Pedido": pedido,
                            "Data": data,
                            "Embal": embal,
                            "Loja": current_loja,
                            "Depósito": deposito,
                            "Qtde Expedir": qtde
                        })

    # Exportar os dados de cada loja para o seu próprio arquivo Excel
    for loja, dados in lojas_data.items():
        if dados:
            df = pd.DataFrame(dados)
            excel_filename = pasta_saida / f"Loja {loja}.xlsx"
            df.to_excel(excel_filename, index=False)
            print(f"Salvo {excel_filename.name} com {len(df)} registros.")
            
    # Ao final da conversão, aciona automaticamente o script consolidado
    print("\nExecutando a geração do arquivo consolidado...")
    script_dashboard = base_dir / "2-consolidado.py"
    try:
        subprocess.run([sys.executable, str(script_dashboard)], check=True)
    except Exception as e:
        print(f"Ocorreu um erro ao rodar o script consolidado.py: {e}")

if __name__ == "__main__":
    parse_pdfs()
