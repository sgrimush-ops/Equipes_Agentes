import os
import pandas as pd
from actions.base_action import BaseAction

class AcaoPrepararDados(BaseAction):
    @property
    def name(self) -> str:
        return "Preparar CSV Pedido de Loja"
        
    @property
    def description(self) -> str:
        return "Converte e formata o arquivo 'pedido.xlsx' em um arquivo 'digitar.csv'."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        input_file = 'bd_entrada/pedido.xlsx'
        output_file = 'bd_saida/digitar.csv'
        
        if update_callback:
            update_callback({'status': 'Preparando dados...', 'log': f"Lendo {input_file}..."})

        # Verifica bloqueios antes de iniciar
        if stop_event and stop_event.is_set(): return

        try:
            # Lê o Excel original
            df = pd.read_excel(input_file, dtype=str)
            
            # Pausa intermediária se necessária
            if pause_event and pause_event.is_set():
                if update_callback: update_callback({'status': 'PAUSADO'})
                while pause_event.is_set():
                    if stop_event and stop_event.is_set(): return
                    import time
                    time.sleep(0.5)
                if update_callback: update_callback({'status': 'Preparando dados...'})

            # Remover colunas indesejadas
            cols_to_drop = ['Data Pedido', 'Usuários', 'Qtd Lançamentos']
            df = df.drop(columns=[col for col in cols_to_drop if col in df.columns], errors='ignore')

            # Renomear colunas
            rename_map = {
                'Loja': 'Código Empresa',
                'Descrição': 'Empresa : Produto',
                'Código Consinco': 'Código Produto',
                'Emb': 'Embalagem Compra',
                'Total CX': 'Pedir'
            }
            df = df.rename(columns=rename_map)

            # Preenchimento de nulos para garantir que as colunas fiquem preenchidas
            for col in rename_map.values():
                if col not in df.columns:
                    df[col] = ''
            
            # Garantir ordenação básica
            df_final = df.copy()
            
            if stop_event and stop_event.is_set(): return
            
            # Salva em CSV com separador ;
            df_final.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
            
            msg = f"Arquivo '{output_file}' gerado com sucesso. Total de registros: {len(df_final)}"
            if update_callback:
                update_callback({'status': 'Concluído', 'finished': True, 'log': msg})
                
        except FileNotFoundError:
            if update_callback:
                update_callback({'error': f"O arquivo '{input_file}' não foi encontrado na pasta."})
        except Exception as e:
            if update_callback:
                update_callback({'error': f"Erro inesperado ao converter planilha: {str(e)}"})

    def has_calibration(self) -> bool:
        return False
        
    def calibrate(self, parent_window):
        pass

def get_action():
    return AcaoPrepararDados()
