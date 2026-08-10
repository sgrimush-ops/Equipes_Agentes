import pandas as pd
import pyautogui
import time
import os
import json
from pynput import keyboard
from pynput.mouse import Button as PynButton, Controller as PynMouse

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

class AbastecimentoProcessor:
    def __init__(self):
        self.coords = self.load_coordinates()
        self._mouse = PynMouse()

    def _click(self, coord, double_click=False):
        """Clique preciso via pynput."""
        self._mouse.position = (coord[0], coord[1])
        time.sleep(0.05)
        if double_click:
            self._mouse.click(PynButton.left, 2)
        else:
            self._mouse.click(PynButton.left)
        time.sleep(0.1)

    def load_coordinates(self):
        coords_path = 'coords/coords.json'
        if not os.path.exists(coords_path):
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            coords_path = os.path.join(base_path, 'coords', 'coords.json')
            
        if not os.path.exists(coords_path):
            return None
            
        with open(coords_path, 'r') as f:
            return json.load(f)

    def _normalize_header(self, value):
        txt = str(value).strip().upper()
        txt = txt.replace('Á', 'A').replace('À', 'A').replace('Â', 'A').replace('Ã', 'A')
        txt = txt.replace('É', 'E').replace('Ê', 'E')
        txt = txt.replace('Í', 'I')
        txt = txt.replace('Ó', 'O').replace('Ô', 'O').replace('Õ', 'O')
        txt = txt.replace('Ú', 'U').replace('Ç', 'C')
        txt = txt.replace(' ', '').replace('_', '').replace(':', '')
        return txt

    def _find_column(self, columns, aliases):
        normalized = {col: self._normalize_header(col) for col in columns}
        alias_set = {self._normalize_header(a) for a in aliases}

        for col, norm in normalized.items():
            if norm in alias_set:
                return col

        for col, norm in normalized.items():
            if any(norm.startswith(a) for a in alias_set):
                return col

        return None

    def run(self, update_callback=None, stop_event=None, pause_event=None):
        if not self.coords:
            msg = "Arquivo 'coords/coords.json' não encontrado. Calibre primeiro."
            if update_callback: update_callback({'error': msg})
            return

        req_keys = [
            "campo_codigo_abastecimento",
            "botao_familia_abastecimento",
            "aba_divisao_abastecimento",
            "linha_categoria_abastecimento",
            "campo_forma_abastecimento",
            "posicao_M_abastecimento",
            "posicao_C_abastecimento",
            "posicao_L_abastecimento",
            "posicao_I_abastecimento"
        ]
        
        faltantes = [k for k in req_keys if k not in self.coords]
        if faltantes:
            msg = f"Coordenadas não calibradas: {', '.join(faltantes)}. Calibre primeiro."
            if update_callback: update_callback({'error': msg})
            return

        def on_press(key):
            if key == keyboard.Key.esc:
                if stop_event: stop_event.set()
                return False 
        
        esc_listener = keyboard.Listener(on_press=on_press)
        esc_listener.start()

        input_file = 'bd_entrada/forma_abastecimento.xlsx'
        if not os.path.exists(input_file):
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            input_file = os.path.join(base_path, 'bd_entrada', 'forma_abastecimento.xlsx')
            
        if not os.path.exists(input_file):
            msg = f"Arquivo '{input_file}' não encontrado na pasta bd_entrada."
            if update_callback: update_callback({'error': msg})
            return

        try:
            if update_callback: update_callback({'status': "Lendo planilha de abastecimento..."})
            df = pd.read_excel(input_file, dtype=str)
            
            col_produto = self._find_column(df.columns, ['PRODUTO', 'CODIGOPRODUTO', 'CODIGO PRODUTO'])
            col_abastecimento = self._find_column(df.columns, ['ABASTECIMENTO', 'FORMADEABASTECIMENTO', 'FORMA'])

            if not col_produto or not col_abastecimento:
                msg = "Colunas obrigatórias não encontradas: PRODUTO e ABASTECIMENTO."
                if update_callback: update_callback({'error': msg})
                return
            
            total_linhas = len(df)
            
            if total_linhas == 0:
                if update_callback: update_callback({'error': "Nenhum dado encontrado na planilha."})
                return

            if update_callback: update_callback({'status': "Iniciando em 5 segundos... Clique na janela do ERP!"})
            for i in range(5, 0, -1):
                if stop_event and stop_event.is_set():
                    return
                if update_callback: update_callback({'status': f"Iniciando em {i} segundos..."})
                time.sleep(1)

            # Início do loop
            for idx, row in df.iterrows():
                if stop_event and stop_event.is_set():
                    if update_callback: update_callback({'status': "Processo abortado pelo usuário (ESC)."})
                    break
                    
                while pause_event and pause_event.is_set():
                    time.sleep(0.5)

                produto = str(row[col_produto]).strip().replace('.0', '')
                if not produto or produto.lower() == 'nan':
                    continue
                    
                forma = str(row[col_abastecimento]).strip().upper()
                
                # Mapeamento da forma para a coordenada
                coord_forma = None
                if forma == 'M':
                    coord_forma = self.coords['posicao_M_abastecimento']
                elif forma == 'C':
                    coord_forma = self.coords['posicao_C_abastecimento']
                elif forma == 'L':
                    coord_forma = self.coords['posicao_L_abastecimento']
                elif forma == 'I':
                    coord_forma = self.coords['posicao_I_abastecimento']
                else:
                    if update_callback: update_callback({'status': f"PULANDO {idx+1}/{total_linhas}: Forma '{forma}' inválida para o produto {produto}."})
                    continue

                if update_callback: update_callback({'status': f"Processando {idx+1}/{total_linhas}: Produto {produto} - Forma {forma}"})

                # 1. Pressiona F2 para limpar/preparar a tela
                pyautogui.press('f2')
                time.sleep(0.5)
                
                # 1.5 Clica no campo de código do produto
                self._click(self.coords['campo_codigo_abastecimento'])
                time.sleep(0.2)
                
                # 2. Digita código do produto
                pyautogui.write(produto, interval=0.05)
                time.sleep(0.3)
                
                # 3. Pressiona F8 para carregar
                pyautogui.press('f8')
                time.sleep(1.2)
                
                # 4. Clica no botão de família
                self._click(self.coords['botao_familia_abastecimento'])
                time.sleep(1.0) # Aguarda abrir a tela de família
                
                # 5. Clica na aba divisão
                self._click(self.coords['aba_divisao_abastecimento'])
                time.sleep(0.5)
                
                # 6. Duplo clique na categoria
                self._click(self.coords['linha_categoria_abastecimento'], double_click=True)
                time.sleep(0.8) # Aguarda carregar a sub-tela
                
                # 7. Clica no campo dropdown de forma de abastecimento
                self._click(self.coords['campo_forma_abastecimento'])
                time.sleep(0.4)
                
                # 8. Clica na opção correspondente (M, C, L, I)
                self._click(coord_forma)
                time.sleep(0.4)
                
                # 9. Tecla f4 (salvar)
                pyautogui.press('f4')
                time.sleep(1.0)
                
                # 10. Tecla f10 duas vezes (fechar aba da categoria, depois aba da família)
                pyautogui.press('f10')
                time.sleep(0.5)
                pyautogui.press('f10')
                time.sleep(0.8)

            if update_callback and not (stop_event and stop_event.is_set()):
                update_callback({'status': "Processamento finalizado com sucesso!", 'done': True})

        except Exception as e:
            if update_callback: update_callback({'error': f"Erro crítico: {str(e)}"})
