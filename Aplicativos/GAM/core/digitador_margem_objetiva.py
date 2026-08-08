import pandas as pd
import pyautogui
import time
import os
import json
from pynput import keyboard
from pynput.mouse import Button as PynButton, Controller as PynMouse

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

class MargemObjetivaProcessor:
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

        req_keys = ["campo_familia_margem", "aba_divisao_margem", "linha_divisao_margem", "campo_preenchimento_margem"]
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

        input_file = 'bd_entrada/margens.xlsx'
        if not os.path.exists(input_file):
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            input_file = os.path.join(base_path, 'bd_entrada', 'margens.xlsx')
            
        if not os.path.exists(input_file):
            msg = f"Arquivo '{input_file}' não encontrado na pasta bd_entrada."
            if update_callback: update_callback({'error': msg})
            return

        try:
            if update_callback: update_callback({'status': "Lendo planilha margens..."})
            df = pd.read_excel(input_file, dtype=str)
            
            col_familia = self._find_column(df.columns, ['CODIGOFAMILIA', 'CODIGO FAMILIA', 'FAMILIA'])
            col_margem = self._find_column(df.columns, ['MARGEM', 'MARGEMOBJETIVA'])

            if not col_familia or not col_margem:
                msg = "Colunas obrigatórias não encontradas: CODIGO_FAMILIA e MARGEM."
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

                familia = str(row[col_familia]).strip()
                margem = str(row[col_margem]).strip().replace('%', '') # Remove % se houver
                
                # Se margem tiver decimal, verificar se precisa converter ponto ou virgula, o sistema consinco usa virgula
                margem = margem.replace('.', ',')

                if update_callback: update_callback({'status': f"Processando {idx+1}/{total_linhas}: Família {familia} - Margem {margem}%"})

                # 1. Clica no campo mapeado para digitar o código da família
                self._click(self.coords['campo_familia_margem'])
                
                # 2. Digita código
                pyautogui.write(familia)
                time.sleep(0.3)
                
                # Pressiona F8 para consultar/buscar o item para tela (padrão Consinco)
                pyautogui.press('f8')
                time.sleep(1.0)
                
                # 3. Clica na aba divisão mapeada
                self._click(self.coords['aba_divisao_margem'])
                time.sleep(0.5)
                
                # 4. Duplo clique na linha mapeada
                self._click(self.coords['linha_divisao_margem'], double_click=True)
                time.sleep(0.5)
                
                # 5. Duplo clique na área de preenchimento de margem para subscrever valor existente
                self._click(self.coords['campo_preenchimento_margem'], double_click=True)
                time.sleep(0.2)
                
                # 6. Digita o valor numérico da margem
                pyautogui.write(margem)
                time.sleep(0.3)
                
                # 7. Tecla f4 (salvar)
                pyautogui.press('f4')
                time.sleep(1.0)
                
                # 8. Tecla f10 (fechar aba)
                pyautogui.press('f10')
                time.sleep(0.8)
                
                # 9. Finaliza com f2 (limpar)
                pyautogui.press('f2')
                time.sleep(0.5)

            if update_callback and not (stop_event and stop_event.is_set()):
                update_callback({'status': "Processamento finalizado com sucesso!", 'done': True})

        except Exception as e:
            if update_callback: update_callback({'error': f"Erro crítico: {str(e)}"})
