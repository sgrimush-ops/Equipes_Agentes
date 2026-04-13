import pandas as pd
from pathlib import Path
import os
import subprocess
import sys
from datetime import datetime

def processar_pedidos_pendentes():
    # Descobre o diretório real da pasta base 'Aplicativos' para não depender de caminhos hardcoded
    base_dir = Path(__file__).resolve().parent.parent

    # Caminho do arquivo de origem (a query recém criada)
    arquivo_origem = base_dir / 'import_querys' / 'ped_pendentes.txt'
    
    # Pasta de destino e arquivo
    pasta_destino = base_dir / 'pendencias' / 'bd_saida'
    pasta_destino.mkdir(parents=True, exist_ok=True)
    
    data_hoje = datetime.now().strftime('%d_%m_%Y')
    arquivo_csv_saida = pasta_destino / f'ped_pendentes_formatado_{data_hoje}.csv'

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando leitura de: {arquivo_origem.name}")

    try:
        # Lê o TXT bruto delimitado por ponto-e-vírgula (Padrão Consinco), 
        # forçando object puro para evitar interpretação de floats errada
        df = pd.read_csv(arquivo_origem, sep=';', dtype=str, encoding='utf-8')
        
        # Limpeza genérica: Remove espaços em branco desnecessários de chaves textuais (strings)
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()
                
        # Saneamento Específico: Limpar timestamps lixo do Consinco (ex: 2026-03-31-00.00.00.000000 -> 2026-03-31)
        if 'DATA' in df.columns:
            df['DATA'] = df['DATA'].astype(str).str[:10]
                
        # Grava os resultados garantindo que o CSV seja gerado com codificação pt-BR do Excel e decimais nativos
        df.to_csv(arquivo_csv_saida, index=False, sep=';', encoding='utf-8-sig')
        
        print(f"✅ SUCESSO! Arquivo processado e formatado isolado com sucesso.")
        print(f"Salvo em: {arquivo_csv_saida}")
        print(f"Total de Linhas Processadas: {len(df)}")
        return True
        
    except FileNotFoundError:
        print(f"❌ ERRO: O arquivo central não foi encontrado em \n{arquivo_origem}")
        print("💡 Verifique se a query SQL foi devidamente extraída/puxada com o nome 'ped_pendentes.txt'.")
        return False
    except Exception as e:
        print(f"❌ ERRO CRÍTICO no processamento: {str(e)}")
        return False

if __name__ == '__main__':
    # Trava o ambiente de execução da VENV no local do diretório pai para importações dinâmicas Python
    os.chdir(Path(__file__).parent.resolve())
    sucesso = processar_pedidos_pendentes()
    if sucesso:
        script_dashboard = Path(__file__).parent / '2-dashboard_pendencias.py'
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Executando dashboard: {script_dashboard.name}")
        subprocess.run([sys.executable, str(script_dashboard)], check=True)
