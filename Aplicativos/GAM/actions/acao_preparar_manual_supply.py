import pandas as pd
import os
import math
import time
from pathlib import Path
from actions.base_action import BaseAction

class AcaoPrepararSuplay(BaseAction):
    @property
    def name(self) -> str:
        return "Preparar CSV Pedido Supply"
        
    @property
    def description(self) -> str:
        return "Prepara os dados do arquivo 'query.parquet' gerando 'digitar.csv'."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if update_callback:
            update_callback({'status': 'Preparando dados...', 'log': "Procurando arquivo manual (Excel ou CSV)..."})
            
        if stop_event and stop_event.is_set(): return

        try:
            parquet_path = Path('c:/Users/Alessandro.soares.BAKLIZI/Downloads/Equipes_Agentes/Aplicativos/import_querys/query.parquet')
            if parquet_path.exists():
                if update_callback:
                    update_callback({'log': "Lendo arquivo query.parquet..."})
                df = pd.read_parquet(parquet_path)
            else:
                if update_callback:
                    update_callback({'error': "Arquivo 'query.parquet' não encontrado na pasta 'import_querys'."})
                return
        except Exception as e:
            if update_callback:
                update_callback({'error': f"Erro ao ler o arquivo: {e}"})
            return

        if pause_event and pause_event.is_set():
            if update_callback: update_callback({'status': 'PAUSADO'})
            while pause_event.is_set():
                if stop_event and stop_event.is_set(): return
                time.sleep(0.5)
            if update_callback: update_callback({'status': 'Preparando dados...'})

        # Mapeamento para as colunas do novo query.parquet (Sincronizado com SQL Mestre)
        col_disp = 'QUANTIDADE_DISPONIVEL'
        col_pend = 'QTD_PEND_PEDCOMPRA'
        col_min  = 'QUANTIDADE_ESTOQUE_MINIMO'
        col_max  = 'QUANTIDADE_ESTOQUE_MAXIMO'
        col_emb  = 'EMBL_TRANSFERENCIA'
        col_empresa = 'CODIGO_EMPRESA'
        col_produto = 'CODIGO_PRODUTO'

        df['Pedir'] = 0

        if col_emb in df.columns:
            df[col_emb] = df[col_emb].astype(str).str.replace(r'\D', '', regex=True)
            df.loc[df[col_emb] == '', col_emb] = '1'
            df[col_emb] = pd.to_numeric(df[col_emb], errors='coerce').fillna(1)
            df[col_emb] = df[col_emb].apply(lambda x: 1 if x == 0 else x)
        else:
            df[col_emb] = 1

        if col_empresa in df.columns:
            df = df.dropna(subset=[col_empresa])
            df[col_empresa] = pd.to_numeric(df[col_empresa], errors='coerce')
        
        for col in [col_disp, col_pend, col_min, col_max]:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['disp_calc'] = df[col_disp].apply(lambda x: x if x > 0 else 0)

        def calcular_pedir(row):
            disp = row['disp_calc']
            pend = row[col_pend]
            minimo = row[col_min]
            maximo = row[col_max]
            emb = row[col_emb]
            
            if (disp + pend) < minimo:
                valor = (maximo - (disp + pend)) / emb
                return valor if valor > 0 else 0
            else:
                return 0

        df['Pedir'] = df.apply(calcular_pedir, axis=1)

        if stop_event and stop_event.is_set(): return

        # 3. Verificar o estoque disponivel na loja 15
        loja15 = df[df[col_empresa] == 15]
        
        estoque_loja15 = {}
        for _, row in loja15.iterrows():
            est = row[col_disp]
            estoque_loja15[row[col_produto]] = est if est > 0 else 0

        def verificar_loja15(row):
            pedir_atual = row['Pedir']
            produto = row[col_produto]
            
            if pedir_atual <= 0:
                return 0
                
            est_15 = estoque_loja15.get(produto, 0)
            
            if est_15 > 0:
                return pedir_atual
            else:
                return 0

        df['Pedir'] = df.apply(verificar_loja15, axis=1)

        def arredondar_customizado(valor):
            if pd.isna(valor):
                return 0
            parte_inteira = math.floor(valor)
            parte_decimal = valor - parte_inteira
            
            if parte_decimal < 0.4:
                return int(parte_inteira)
            else:
                return int(parte_inteira + 1)

        df['Pedir'] = df['Pedir'].apply(arredondar_customizado)
        
        idx_pedir = df.columns.get_loc('Pedir')
        estoques_cd_bruto = df[col_produto].map(lambda x: estoque_loja15.get(x, 0))
        df.insert(idx_pedir + 1, 'Estq_CD_cx', round(estoques_cd_bruto / df[col_emb], 2))
        
        df = df.drop(columns=['disp_calc'])
        
        df_resultado = df[(df['Pedir'] > 0) & (df[col_empresa] != 15)].copy()
        df_resultado[col_empresa] = df_resultado[col_empresa].apply(lambda x: str(int(float(x))).zfill(3))
        
        # Renomeia para compatibilidade com o robô de digitação (OrderProcessorSupply)
        df_resultado = df_resultado.rename(columns={col_produto: 'CODIGO_CONSINCO', 'DESCRICAO_PRODUTO': 'descricao'})
        
        arquivo_saida = 'bd_saida/digitar.csv'
        
        try:
            df_resultado.to_csv(arquivo_saida, index=False, sep=';', encoding='utf-8-sig', decimal=',')
            msg = f"Arquivo '{arquivo_saida}' gerado com sucesso com {len(df_resultado)} linhas!"
            if update_callback:
                update_callback({'status': 'Concluído', 'finished': True, 'log': msg})
        except Exception as e:
            if update_callback:
                update_callback({'error': f"Erro ao salvar '{arquivo_saida}': {e}"})

    def has_calibration(self) -> bool:
        return False
        
    def calibrate(self, parent_window):
        pass

def get_action():
    return AcaoPrepararSuplay()
