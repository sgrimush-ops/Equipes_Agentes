import pandas as pd
import pyautogui
import time
import os
import json
from pynput import keyboard
from pynput.mouse import Button as PynButton, Controller as PynMouse

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

class AbastecimentoFamiliaProcessor:
    def __init__(self):
        self.coords = self.load_coordinates() or {}
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
            return {}
            
        try:
            with open(coords_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _get_coord(self, primary_key, fallback_keys=None):
        if fallback_keys is None:
            fallback_keys = []
        if primary_key in self.coords and self.coords[primary_key]:
            return self.coords[primary_key]
        for fb in fallback_keys:
            if fb in self.coords and self.coords[fb]:
                return self.coords[fb]
        return None

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
        self.coords = self.load_coordinates() or {}

        coord_campo_familia = self._get_coord('campo_familia_abast_fam', ['campo_familia_margem'])
        coord_aba_divisao = self._get_coord('aba_divisao_abast_fam', ['aba_divisao_margem', 'aba_divisao_abastecimento'])
        coord_linha_divisao = self._get_coord('linha_divisao_abast_fam', ['linha_divisao_margem', 'linha_categoria_abastecimento'])
        coord_campo_forma = self._get_coord('campo_forma_abast_fam', ['campo_forma_abastecimento'])
        coord_pos_m = self._get_coord('posicao_M_abast_fam', ['posicao_M_abastecimento'])
        coord_pos_c = self._get_coord('posicao_C_abast_fam', ['posicao_C_abastecimento'])
        coord_pos_l = self._get_coord('posicao_L_abast_fam', ['posicao_L_abastecimento'])
        coord_pos_i = self._get_coord('posicao_I_abast_fam', ['posicao_I_abastecimento'])

        faltantes = []
        if not coord_campo_familia: faltantes.append("Campo Código Família")
        if not coord_aba_divisao: faltantes.append("Aba Divisão")
        if not coord_linha_divisao: faltantes.append("Linha Divisão/Categoria")
        if not coord_campo_forma: faltantes.append("Dropdown Abastecimento")
        if not coord_pos_m: faltantes.append("Posição M")
        if not coord_pos_c: faltantes.append("Posição C")
        if not coord_pos_l: faltantes.append("Posição L")
        if not coord_pos_i: faltantes.append("Posição I")

        if faltantes:
            msg = f"Coordenadas não calibradas: {', '.join(faltantes)}. Calibre primeiro."
            if update_callback: update_callback({'error': msg})
            return

        coords_forma_map = {
            'M': coord_pos_m,
            'C': coord_pos_c,
            'L': coord_pos_l,
            'I': coord_pos_i
        }

        # Listener do teclado para parar com ESC
        def on_press(key):
            if key == keyboard.Key.esc:
                if stop_event: stop_event.set()
                return False 
        
        esc_listener = keyboard.Listener(on_press=on_press)
        esc_listener.start()

        input_file = 'bd_entrada/abastecimento_familia.xlsx'
        if not os.path.exists(input_file):
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            input_file = os.path.join(base_path, 'bd_entrada', 'abastecimento_familia.xlsx')
            
        if not os.path.exists(input_file):
            msg = f"Arquivo '{input_file}' não encontrado na pasta bd_entrada."
            if update_callback: update_callback({'error': msg})
            return

        try:
            if update_callback: update_callback({'status': "Lendo planilha abastecimento_familia.xlsx..."})
            df = pd.read_excel(input_file, dtype=str)
            
            col_familia = self._find_column(df.columns, ['SEQFAMILIA', 'CODIGOFAMILIA', 'CODIGO_FAMILIA', 'FAMILIA', 'SEQ_FAMILIA', 'COD_FAMILIA'])
            col_abastecimento = self._find_column(df.columns, ['FORM_ABAST', 'FORMADEABASTECIMENTO', 'FORMA_ABAST', 'FORMA_ABASTECIMENTO', 'ABASTECIMENTO', 'FORMA'])

            if not col_familia or not col_abastecimento:
                msg = f"Colunas obrigatórias não encontradas na planilha. Detectado: {list(df.columns)}. Necessário: Família (ex: SEQFAMILIA) e Forma de Abastecimento (ex: Form_Abast)."
                if update_callback: update_callback({'error': msg})
                return
            
            # Limpa e filtra dados
            df = df.dropna(subset=[col_familia, col_abastecimento])
            df = df[df[col_familia].astype(str).str.strip().str.lower() != 'nan']
            df = df[df[col_familia].astype(str).str.strip() != '']
            
            # Remove duplicatas de famílias mantendo a primeira ocorrência
            df_familias = df.drop_duplicates(subset=[col_familia], keep='first')
            total_familias = len(df_familias)
            
            if total_familias == 0:
                if update_callback: update_callback({'error': "Nenhuma família válida encontrada na planilha."})
                return

            if update_callback: update_callback({'status': f"Encontradas {total_familias} famílias únicas. Iniciando em 5 segundos... Fique na tela de Família no ERP!"})
            for i in range(5, 0, -1):
                if stop_event and stop_event.is_set():
                    return
                if update_callback: update_callback({'status': f"Iniciando em {i} segundos..."})
                time.sleep(1)

            # Início do loop
            for idx, (_, row) in enumerate(df_familias.iterrows()):
                if stop_event and stop_event.is_set():
                    if update_callback: update_callback({'status': "Processo abortado pelo usuário (ESC)."})
                    break
                    
                while pause_event and pause_event.is_set():
                    time.sleep(0.5)

                familia = str(row[col_familia]).strip().replace('.0', '')
                forma = str(row[col_abastecimento]).strip().upper()

                if forma not in coords_forma_map:
                    if update_callback: update_callback({'status': f"PULANDO [{idx+1}/{total_familias}]: Família {familia} com forma '{forma}' inválida (aceito: M, C, L, I)."})
                    continue

                coord_opcao_forma = coords_forma_map[forma]

                if update_callback: update_callback({'status': f"Processando [{idx+1}/{total_familias}]: Família {familia} -> Forma {forma}"})

                # 1. Clica no campo de código da família
                self._click(coord_campo_familia)
                time.sleep(0.2)
                
                # 2. Digita código da família
                pyautogui.write(familia, interval=0.03)
                time.sleep(0.3)
                
                # 3. Pressiona F8 para consultar a família
                pyautogui.press('f8')
                time.sleep(1.2)
                
                # 4. Clica na aba divisão
                self._click(coord_aba_divisao)
                time.sleep(0.5)
                
                # 5. Duplo clique na linha da divisão/categoria
                self._click(coord_linha_divisao, double_click=True)
                time.sleep(0.8)
                
                # 6. Clica no campo dropdown de forma de abastecimento
                self._click(coord_campo_forma)
                time.sleep(1.5)
                
                # 7. Clica na opção correspondente (M, C, L, I)
                self._click(coord_opcao_forma)
                time.sleep(1.2)
                
                # 8. Tecla F4 (salvar)
                pyautogui.press('f4')
                time.sleep(1.0)
                
                # 9. Tecla F10 (fechar sub-aba da divisão)
                pyautogui.press('f10')
                time.sleep(0.8)
                
                # 10. Tecla F2 (limpar tela da família para o próximo ciclo)
                pyautogui.press('f2')
                time.sleep(0.5)

            if update_callback and not (stop_event and stop_event.is_set()):
                update_callback({'status': f"Manutenção de Abastecimento por Família concluída com sucesso! ({total_familias} famílias processadas)", 'done': True})

        except Exception as e:
            if update_callback: update_callback({'error': f"Erro crítico: {str(e)}"})
