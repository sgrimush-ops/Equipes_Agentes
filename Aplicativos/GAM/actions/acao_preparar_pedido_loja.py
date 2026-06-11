import os
import pandas as pd
import math
import subprocess
from pathlib import Path
from actions.base_action import BaseAction


def _resolver_arquivo_entrada(base_dir: Path) -> Path:
    candidatos = [
        base_dir / 'bd_entrada' / 'pedido.xlsx',
        base_dir / 'bd_entrada' / 'pedidos.xlsx',
    ]
    for caminho in candidatos:
        if caminho.exists():
            return caminho
    return candidatos[0]


class AcaoPrepararDados(BaseAction):
    @staticmethod
    def _parse_numeric_value(value, default=0.0):
        if pd.isna(value):
            return default

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text or text.lower() in {'nan', 'none'}:
            return default

        text = text.replace(' ', '')
        negative = text.startswith('-')
        if negative:
            text = text[1:]

        if ',' in text and '.' in text:
            if text.rfind(',') > text.rfind('.'):
                text = text.replace('.', '').replace(',', '.')
            else:
                text = text.replace(',', '')
        elif ',' in text:
            text = text.replace(',', '.')
        elif text.count('.') > 1:
            integer_part, decimal_part = text.rsplit('.', 1)
            text = integer_part.replace('.', '') + '.' + decimal_part

        try:
            number = float(text)
        except ValueError:
            return default

        return -number if negative else number

    @classmethod
    def _parse_numeric_series(cls, series, default=0.0):
        if pd.api.types.is_numeric_dtype(series):
            return series.fillna(default)
        return series.apply(
            lambda value: cls._parse_numeric_value(value, default=default)
        )

    @property
    def name(self) -> str:
        return "Preparar CSV Pedido de Loja"
        
    @property
    def description(self) -> str:
        return "Converte e formata o arquivo 'pedido.xlsx' (ou 'pedidos.xlsx') em um arquivo 'digitar.csv'."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        input_file = _resolver_arquivo_entrada(base_dir)
        output_file = base_dir / 'bd_saida' / 'digitar.csv'
        
        if update_callback:
            update_callback({'status': 'Preparando dados...', 'log': f"Lendo {input_file.name}..."})

        if stop_event and stop_event.is_set(): return

        try:
            # Lê o Excel original
            df_excel = pd.read_excel(input_file)
            
            if pause_event and pause_event.is_set():
                if update_callback: update_callback({'status': 'PAUSADO'})
                while pause_event.is_set():
                    if stop_event and stop_event.is_set(): return
                    import time
                    time.sleep(0.5)
                if update_callback: update_callback({'status': 'Preparando dados...'})

            # Limpar espaços no nome das colunas
            df_excel.columns = [str(col).strip() for col in df_excel.columns]

            # Mapeamento robusto por substring
            col_loja = None
            col_cod = None
            col_desc = None
            col_emb = None
            col_pedir = None

            for col in df_excel.columns:
                col_lower = col.lower()
                if 'loja' in col_lower:
                    col_loja = col
                elif 'consinco' in col_lower:
                    col_cod = col
                elif 'desc' in col_lower:
                    col_desc = col
                elif 'emb' in col_lower:
                    col_emb = col
                elif 'total' in col_lower or 'pedir' in col_lower or 'cx' in col_lower:
                    col_pedir = col

            # Fallback secundário se não achou código por consinco
            if not col_cod:
                for col in df_excel.columns:
                    col_lower = col.lower()
                    if 'codigo' in col_lower or 'código' in col_lower or 'prod' in col_lower:
                        col_cod = col
                        break

            # Validar e fallback se necessário
            if not col_loja:
                raise ValueError("Coluna 'Loja' não encontrada na planilha.")
            if not col_cod:
                raise ValueError("Coluna de Código de Produto (Consinco) não encontrada na planilha.")
            if not col_pedir:
                raise ValueError("Coluna de quantidade ('Total CX') não encontrada na planilha.")

            # Limpar e converter colunas fundamentais
            df_excel[col_loja] = self._parse_numeric_series(df_excel[col_loja], default=0).round(0).astype(int)
            df_excel[col_cod] = self._parse_numeric_series(df_excel[col_cod], default=0).round(0).astype(int)
            df_excel[col_pedir] = self._parse_numeric_series(df_excel[col_pedir], default=0)
            
            # Garantir coluna Emb (embalagem)
            if col_emb and col_emb in df_excel.columns:
                df_excel[col_emb] = self._parse_numeric_series(df_excel[col_emb], default=1)
                df_excel[col_emb] = df_excel[col_emb].apply(lambda x: 1 if x == 0 else x)
            else:
                df_excel[col_emb] = 1

            # Criar df com estrutura final
            df_final = pd.DataFrame()
            df_final['CODIGO_EMPRESA'] = df_excel[col_loja]
            df_final['CODIGO_PRODUTO'] = df_excel[col_cod]
            df_final['DESCRICAO'] = df_excel[col_desc] if col_desc and col_desc in df_excel.columns else ''
            df_final['Pedir'] = df_excel[col_pedir]
            df_final['EMBL_TRANSFERENCIA'] = df_excel[col_emb]
            df_final['EMBL_COMPRA'] = df_excel[col_emb] # fallback
            
            # Arredondar customizado para Pedir
            def arredondar_customizado(valor):
                if pd.isna(valor):
                    return 0
                if valor <= 0:
                    return 0
                return int(math.ceil(valor))
            
            df_final['Pedir'] = df_final['Pedir'].apply(arredondar_customizado)

            # Tenta carregar query.parquet para obter informações extras e o estoque da loja 15 (CD)
            parquet_path = Path('c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/import_querys/query.parquet')
            estoque_loja15 = {}
            df_pq = None
            if parquet_path.exists():
                try:
                    df_pq = pd.read_parquet(parquet_path)
                    df_15 = df_pq[df_pq['CODIGO_EMPRESA'] == 15]
                    for _, row in df_15.iterrows():
                        prod = row['CODIGO_PRODUTO']
                        est = row['QUANTIDADE_DISPONIVEL']
                        try:
                            est_val = float(est) if not pd.isna(est) else 0.0
                        except:
                            est_val = 0.0
                        estoque_loja15[int(float(prod))] = est_val if est_val > 0 else 0.0
                except Exception as e:
                    if update_callback:
                        update_callback({'log': f"Aviso: erro ao ler query.parquet: {e}"})

            # Adicionar Estq_CD_cx
            def calcular_estq_cd(row):
                prod = int(row['CODIGO_PRODUTO'])
                emb = row['EMBL_TRANSFERENCIA']
                if prod in estoque_loja15:
                    return round(estoque_loja15[prod] / emb, 2)
                # se não achar no CD, colocar um valor alto para não filtrar por padrão
                return 999999.0

            df_final['Estq_CD_cx'] = df_final.apply(calcular_estq_cd, axis=1)

            # Trazer outras colunas de query.parquet se possível por mesclagem
            # Colunas originais em query.parquet: 
            # DEPARTAMENTO, COMPRADOR, STATUS_COMPRA, QUANTIDADE_DISPONIVEL, QTD_PEND_PEDCOMPRA, QTD_VENDIDA, QUANTIDADE_ESTOQUE_MINIMO, QUANTIDADE_ESTOQUE_MAXIMO, DATA_CADASTRO_PRODUTO
            colunas_extras = [
                'DEPARTAMENTO', 'COMPRADOR', 'STATUS_COMPRA', 'QUANTIDADE_DISPONIVEL', 
                'QTD_PEND_PEDCOMPRA', 'QTD_VENDIDA', 'QUANTIDADE_ESTOQUE_MINIMO', 
                'QUANTIDADE_ESTOQUE_MAXIMO', 'DATA_CADASTRO_PRODUTO'
            ]

            if df_pq is not None:
                try:
                    # Limpar chaves da parquet
                    df_pq_clean = df_pq.copy()
                    df_pq_clean['CODIGO_EMPRESA'] = self._parse_numeric_series(df_pq_clean['CODIGO_EMPRESA'], default=0).round(0).astype(int)
                    df_pq_clean['CODIGO_PRODUTO'] = self._parse_numeric_series(df_pq_clean['CODIGO_PRODUTO'], default=0).round(0).astype(int)
                    
                    # Remover duplicatas para evitar explosão de linhas
                    df_pq_clean = df_pq_clean.drop_duplicates(subset=['CODIGO_EMPRESA', 'CODIGO_PRODUTO'])

                    # Fazer merge
                    df_merged = pd.merge(
                        df_final, 
                        df_pq_clean[['CODIGO_EMPRESA', 'CODIGO_PRODUTO'] + [col for col in colunas_extras if col in df_pq_clean.columns]], 
                        on=['CODIGO_EMPRESA', 'CODIGO_PRODUTO'], 
                        how='left'
                    )
                    df_final = df_merged
                except Exception as e:
                    if update_callback:
                        update_callback({'log': f"Aviso: erro ao mesclar com query.parquet: {e}"})

            # Garantir a existência de todas as colunas
            for col in colunas_extras:
                if col not in df_final.columns:
                    df_final[col] = ''

            # Garantir formatação de CODIGO_EMPRESA (zfill 3)
            df_final['CODIGO_EMPRESA'] = df_final['CODIGO_EMPRESA'].apply(lambda x: str(int(float(x))).zfill(3))

            # Filtrar somente registros onde Pedir > 0 e a Loja não seja 15 (CD)
            df_final = df_final[(df_final['Pedir'] > 0) & (df_final['CODIGO_EMPRESA'] != '015')].copy()

            # Ordenar por Empresa e Código Produto
            df_final = df_final.sort_values(by=['CODIGO_EMPRESA', 'CODIGO_PRODUTO'])

            # Garantir a ordem exata das colunas igual à do acao_preparar_manual_supply.py
            ordem_colunas = [
                'DEPARTAMENTO', 'COMPRADOR', 'CODIGO_EMPRESA', 'CODIGO_PRODUTO', 
                'DESCRICAO', 'STATUS_COMPRA', 'EMBL_COMPRA', 'EMBL_TRANSFERENCIA', 
                'QUANTIDADE_DISPONIVEL', 'QTD_PEND_PEDCOMPRA', 'QTD_VENDIDA', 
                'QUANTIDADE_ESTOQUE_MINIMO', 'QUANTIDADE_ESTOQUE_MAXIMO', 
                'DATA_CADASTRO_PRODUTO', 'Pedir', 'Estq_CD_cx'
            ]
            
            # Reordenar se todas existirem, senão apenas garantir as colunas
            df_final = df_final.reindex(columns=ordem_colunas)

            if stop_event and stop_event.is_set(): return

            # Salva o arquivo em bd_saida/digitar.csv
            df_final.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig', decimal=',')
            
            msg = f"Arquivo '{output_file}' gerado com sucesso com {len(df_final)} linhas!"
            if update_callback:
                update_callback({'status': 'Concluído', 'finished': True, 'log': msg})

            # Executa o filtro de estoque de CD (estq_cd_maior_q_.py)
            try:
                filtro_path = str(base_dir / 'bd_saida' / 'estq_cd_maior_q_.py')
                subprocess.run(['python', filtro_path], cwd=str(base_dir / 'bd_saida'), check=True)
                if update_callback:
                    update_callback({'log': 'Filtro estq_cd_maior_q_.py executado com sucesso.'})
            except Exception as e:
                if update_callback:
                    update_callback({'log': f"Aviso: erro ao rodar filtro final: {e}"})

        except FileNotFoundError:
            if update_callback:
                update_callback({'error': f"Nenhum arquivo de entrada encontrado em 'bd_entrada' (esperado: {input_file.name})."})
        except Exception as e:
            if update_callback:
                update_callback({'error': f"Erro inesperado ao converter planilha: {str(e)}"})

    def has_calibration(self) -> bool:
        return False
        
    def calibrate(self, parent_window):
        pass

def get_action():
    return AcaoPrepararDados()
