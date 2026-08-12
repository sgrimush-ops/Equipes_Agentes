import pandas as pd
import pyautogui
import time
import os
import json
import cv2
import numpy as np
import glob
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
            col_empresa = self._find_column(df.columns, ['EMPRESA', 'CODIGO EMPRESA', 'LOJA'])
            col_status = self._find_column(df.columns, ['STATUS', 'ACAO', 'AÇÃO'])

            if not col_produto or not col_abastecimento:
                msg = "Colunas obrigatórias não encontradas: PRODUTO e ABASTECIMENTO."
                if update_callback: update_callback({'error': msg})
                return
            
            total_linhas = len(df)
            
            # Pré-carregamento dos templates visual
            templates_cv2 = {'ativo': [], 'inativo': []}
            for stat_name in ['ativo', 'inativo']:
                arquivos = glob.glob(f'captura_tela/status_{stat_name}*.png')
                for path_img in arquivos:
                    tmplt = cv2.imread(path_img)
                    if tmplt is not None: templates_cv2[stat_name].append(tmplt)
            
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
                
                teve_alteracao_mix = False

                # 1. Pressiona F2 para limpar/preparar a tela
                pyautogui.press('f2')
                time.sleep(1.0)
                
                # 1.5 Clica no campo de código do produto
                self._click(self.coords['campo_codigo_abastecimento'])
                time.sleep(0.2)
                
                # 2. Digita código do produto
                pyautogui.write(produto, interval=0.05)
                time.sleep(0.6)
                
                # 3. Pressiona F8 para carregar
                pyautogui.press('f8')
                time.sleep(2.5)
                
                # --- INÍCIO: CHECAGEM DE MIX EMPRESA/SEGMENTO ---
                empresa_val = str(row[col_empresa]).strip() if col_empresa else ''
                status_val = str(row[col_status]).strip().upper() if col_status else ''
                
                if empresa_val and empresa_val.lower() != 'nan' and status_val and status_val.lower() != 'nan':
                    # Determinar quais empresas checar (ex: '15,16' ou '15.16' se Excel converter para decimal)
                    emp_str = empresa_val.replace('.', ',')
                    empresas_req = [e.strip() for e in emp_str.split(',') if e.strip()]
                    
                    if empresas_req:
                        if update_callback: update_callback({'status': f"Verificando status de Mix ({status_val}) na aba Empresa/Segmento..."})
                        
                        # Clica na aba Empresa/Segmento
                        if 'aba_logis_abast_abastecimento' in self.coords:
                            self._click(self.coords['aba_logis_abast_abastecimento'])
                            time.sleep(1.5) # Aguarda abrir a aba
                            
                            try:
                                # Captura tela uma vez para não ficar tirando print a todo momento
                                w_screen, h_screen = pyautogui.size()
                                tela_pil = pyautogui.screenshot(region=(0, 0, w_screen, h_screen))
                                tela_bgr = cv2.cvtColor(np.array(tela_pil), cv2.COLOR_RGB2BGR)
                                
                                for emp in empresas_req:
                                    coord_linha = None
                                    if emp == '15' and 'linha_cd15_abastecimento' in self.coords:
                                        coord_linha = self.coords['linha_cd15_abastecimento']
                                    elif emp == '16' and 'linha_cd16_abastecimento' in self.coords:
                                        coord_linha = self.coords['linha_cd16_abastecimento']
                                    
                                    if coord_linha:
                                        local_y = coord_linha[1]
                                        slice_y1 = max(0, local_y - 15)
                                        slice_y2 = min(h_screen, local_y + 15)
                                        fatia = tela_bgr[slice_y1:slice_y2, :]
                                        
                                        maior_c = 0; mel_est = None
                                        for st_n, t_list in templates_cv2.items():
                                            for t in t_list:
                                                res = cv2.matchTemplate(fatia, t, cv2.TM_CCOEFF_NORMED)
                                                _, mx, _, _ = cv2.minMaxLoc(res)
                                                if mx > maior_c: 
                                                    maior_c = mx
                                                    mel_est = "A" if st_n == "ativo" else "I"
                                        
                                        status_desejado = "A" if status_val in ["A", "ATIVO"] else "I"
                                        if maior_c >= 0.75 and mel_est == status_desejado:
                                            # Já está no status correto, pula
                                            continue
                                            
                                        # Se precisar alterar, clica e digita 'A' ou 'I'
                                        self._click(coord_linha)
                                        time.sleep(0.04)
                                        tecla = 'a' if status_desejado == "A" else 'i'
                                        pyautogui.press(tecla, presses=2, interval=0.01)
                                        teve_alteracao_mix = True
                                        time.sleep(0.4)
                            except Exception as e:
                                if update_callback: update_callback({'error': f"Erro na leitura visual: {e}"})
                                
                            # Retorna para a aba Geral
                            if 'aba_geral_abastecimento' in self.coords:
                                self._click(self.coords['aba_geral_abastecimento'])
                                time.sleep(1.0)
                # --- FIM: CHECAGEM DE MIX EMPRESA/SEGMENTO ---
                
                # 4. Clica no botão de família
                if update_callback: update_callback({'status': f"Definindo forma de abastecimento: {forma}"})
                self._click(self.coords['botao_familia_abastecimento'])
                time.sleep(6.9) # Aguarda abrir a tela de família
                
                # 5. Clica na aba divisão
                self._click(self.coords['aba_divisao_abastecimento'])
                time.sleep(0.5)
                
                # 6. Duplo clique na categoria
                self._click(self.coords['linha_categoria_abastecimento'], double_click=True)
                time.sleep(0.8) # Aguarda carregar a sub-tela
                
                # 7. Clica no campo dropdown de forma de abastecimento
                self._click(self.coords['campo_forma_abastecimento'])
                time.sleep(1.5)
                
                # 8. Clica na opção correspondente (M, C, L, I)
                self._click(coord_forma)
                time.sleep(1.5)
                
                # 9. Tecla f4 (salvar)
                pyautogui.press('f4')
                time.sleep(1.0)
                
                # 10. Tecla f10 duas vezes (fechar aba da categoria, depois aba da família)
                pyautogui.press('f10')
                time.sleep(1.0)
                pyautogui.press('f10')
                time.sleep(1.0)
                
                # 11. Se houve alteração de Mix na aba raiz, salva (F4) antes de ir pro próximo item
                if teve_alteracao_mix:
                    if update_callback: update_callback({'status': "Salvando alterações de Mix (F4)..."})
                    pyautogui.press('f4')
                    time.sleep(1.0)

            if update_callback and not (stop_event and stop_event.is_set()):
                update_callback({'status': "Processamento finalizado com sucesso!", 'done': True})

        except Exception as e:
            if update_callback: update_callback({'error': f"Erro crítico: {str(e)}"})
