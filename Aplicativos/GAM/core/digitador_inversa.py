import pandas as pd
import pyautogui
import time
import os
import json
from pynput import keyboard
from pynput.mouse import Button as PynButton, Controller as PynMouse

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

class InversaProcessor:
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
            # Tenta pegar no caminho absoluto se estiver rodando de outra raiz
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

        # Verifica todas as chaves necessárias
        req_keys = ["familia_inversa", "divisao_inversa", "categoria_inversa", "abastecimento_inversa"]
        faltantes = [k for k in req_keys if k not in self.coords]
        if faltantes:
            msg = f"Coordenadas não calibradas: {', '.join(faltantes)}. Calibre primeiro."
            if update_callback: update_callback({'error': msg})
            return

        # --- Início do ESC Listener (Emergência) ---
        def on_press(key):
            if key == keyboard.Key.esc:
                if stop_event: stop_event.set()
                return False 
        
        esc_listener = keyboard.Listener(on_press=on_press)
        esc_listener.start()
        # --- Fim do ESC Listener ---

        input_file = 'bd_entrada/inversa.xlsx'
        if not os.path.exists(input_file):
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            input_file = os.path.join(base_path, 'bd_entrada', 'inversa.xlsx')
            
        if not os.path.exists(input_file):
            msg = f"Arquivo '{input_file}' não encontrado na pasta bd_entrada."
            if update_callback: update_callback({'error': msg})
            return

        try:
            if update_callback: update_callback({'status': "Lendo planilha inversa..."})
            df = pd.read_excel(input_file, dtype=str)
            
            col_produto = self._find_column(df.columns, ['CODIGO PRODUTO', 'CÓDIGO PRODUTO', 'PRODUTO', 'SEQPRODUTO'])

            if not col_produto:
                msg = "Coluna obrigatória não encontrada: CODIGO PRODUTO."
                if update_callback: update_callback({'error': msg})
                return
            
            df = df.rename(columns={col_produto: 'Código Produto'})
            produtos = df['Código Produto'].dropna().unique()
            total_produtos = len(produtos)
            
            if total_produtos == 0:
                if update_callback: update_callback({'error': "Nenhum produto encontrado na planilha."})
                return

            # Pausa inicial de 5 segundos para o usuário focar no sistema ERP
            if update_callback: update_callback({'status': "Iniciando em 5 segundos... Clique na janela do ERP!"})
            for i in range(5, 0, -1):
                if stop_event and stop_event.is_set():
                    return
                if update_callback: update_callback({'status': f"Iniciando em {i} segundos..."})
                time.sleep(1)

            # Início do loop
            for idx, prod in enumerate(produtos, 1):
                if stop_event and stop_event.is_set():
                    if update_callback: update_callback({'status': "Processo abortado pelo usuário (ESC)."})
                    break
                    
                while pause_event and pause_event.is_set():
                    time.sleep(0.5)

                if update_callback: update_callback({'status': f"Processando {idx}/{total_produtos}: Produto {prod}"})

                # 1. Tecla F2
                pyautogui.press('f2')
                time.sleep(0.3)
                
                # 2. Digita código
                pyautogui.write(str(prod).strip())
                time.sleep(0.3)
                
                # 3. Tecla F8
                pyautogui.press('f8')
                time.sleep(1.0) # Tempo para processar o F8 no ERP
                
                # 4. Clica na Família
                self._click(self.coords['familia_inversa'])
                
                # 5. Aguarda 2 segundos para carregar nova tela
                time.sleep(2.0)
                
                # 6. Clica na Divisão
                self._click(self.coords['divisao_inversa'])
                
                # 7. Duplo clique na Categoria
                self._click(self.coords['categoria_inversa'], double_click=True)
                
                # 8. Clica Forma Abastecimento
                self._click(self.coords['abastecimento_inversa'])
                
                # 9. Tecla 'S' e Enter
                pyautogui.write('s')
                time.sleep(0.2)
                pyautogui.press('enter')
                time.sleep(0.5)
                
                # 10. Salva com F4
                pyautogui.press('f4')
                time.sleep(1.5) # Tempo para salvar
                
                # 11. Sai das telas com duplo F10
                pyautogui.press('f10')
                time.sleep(0.8)
                pyautogui.press('f10')
                
                # Pausa para reiniciar o ciclo (0.8s)
                time.sleep(0.8)

            if update_callback and not (stop_event and stop_event.is_set()):
                update_callback({'status': "Processamento finalizado com sucesso!", 'done': True})

        except Exception as e:
            if update_callback: update_callback({'error': f"Erro crítico: {str(e)}"})
