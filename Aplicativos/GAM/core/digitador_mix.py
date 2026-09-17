import sys
import pandas as pd
import pyautogui
import time
import os
import json
import cv2
import numpy as np
from pynput import keyboard
from pynput.mouse import Button as PynButton, Controller as PynMouse
try:
    from familia_cleaner import FamiliaDescriptionCleaner
except ModuleNotFoundError:
    from core.familia_cleaner import FamiliaDescriptionCleaner

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02 # Reduzido para velocidade turbo

def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class MixProcessor:
    def __init__(self):
        self.base_dir = _get_base_dir()
        self.coords = self.load_coordinates()
        self.familia_cleaner = FamiliaDescriptionCleaner()
        self._mouse = PynMouse()  # Cliques via pynput para paridade DPI (Regra 65)
        self._ocr_engine = None
        self.store_list = [
            "001", "002", "003", "004", "005", "006", "007", "008", 
            "009", "010", "011", "012", "013", "014", "015", "016", 
            "017", "018", "020", "021", "022", "023", "050", "900", 
            "901", "902"
        ]

    def _get_ocr(self):
        if self._ocr_engine is None:
            try:
                import rapidocr_onnxruntime
                self._ocr_engine = rapidocr_onnxruntime.RapidOCR()
            except Exception as e:
                print(f"[MixProcessor] RapidOCR não disponível: {e}")
        return self._ocr_engine

    def _detectar_popup_atencao(self):
        """
        Verifica se surgiu popup de Atenção / Seleção Inversa / Consinco na tela.
        Retorna (True/False, tipo_deteccao).
        """
        # 1. Checagem de título de janela modal ativa (Delphi / Consinco)
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd).strip()
            if title in ["Atenção", "Atencao", "Aviso", "Mensagem"] or \
               title.startswith("Atenção") or title.startswith("Atencao"):
                return True, f"janela_modal ({title})"
        except Exception:
            pass

        # 2. Checagem visual com RapidOCR
        try:
            ocr = self._get_ocr()
            if ocr:
                screenshot = pyautogui.screenshot()
                screenshot_np = np.array(screenshot)
                res, _ = ocr(screenshot_np)
                if res:
                    textos = " ".join([item[1].upper() for item in res])
                    if ("SELECAO INVERSA" in textos and "PULMAO" in textos) or \
                       ("NORMA DE SELECAO" in textos) or \
                       ("NAO PODE SER DIFERENTE" in textos) or \
                       ("ATENCAO" in textos and "NORMA" in textos):
                        return True, "ocr_texto_popup"
        except Exception as e:
            print(f"[MixProcessor] Erro na verificação OCR do popup: {e}")

        # 3. Fallback de Template Matching com limiar rigoroso
        try:
            screenshot = pyautogui.screenshot()
            screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            for tmpl_path in ['captura_tela/popup_consinco.png', 'captura_tela/aviso.png', 'captura_tela/aviso_icone.png']:
                if os.path.exists(tmpl_path):
                    tmpl = cv2.imread(tmpl_path)
                    if tmpl is not None:
                        res = cv2.matchTemplate(screenshot_bgr, tmpl, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(res)
                        if max_val >= 0.85:
                            return True, f"template_{tmpl_path}"
        except Exception:
            pass

        return False, None

    def _salvar_print_debug(self, nome_arquivo, draw_point=None, info_texto=""):
        """
        Salva uma captura de tela para gravação e diagnóstico visual do processo.
        Se draw_point=(x, y) for passado, desenha um alvo visual em vermelho no ponto exato.
        """
        try:
            grava_dir = 'captura_tela/gravacao'
            os.makedirs(grava_dir, exist_ok=True)
            shot = pyautogui.screenshot()
            img_bgr = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
            if draw_point:
                px, py = int(draw_point[0]), int(draw_point[1])
                cv2.circle(img_bgr, (px, py), 14, (0, 0, 255), 2)
                cv2.circle(img_bgr, (px, py), 3, (0, 0, 255), -1)
                cv2.line(img_bgr, (px - 20, py), (px + 20, py), (0, 0, 255), 1)
                cv2.line(img_bgr, (px, py - 20), (px, py + 20), (0, 0, 255), 1)
            
            caminho_img = os.path.join(grava_dir, f"{nome_arquivo}.png")
            cv2.imwrite(caminho_img, img_bgr)
            
            # Grava no log texto
            log_path = os.path.join(grava_dir, "log_execucao.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {nome_arquivo}: {info_texto} (Ponto: {draw_point})\n")
        except Exception as e:
            print(f"[MixProcessor] Aviso ao salvar print de debug: {e}")

    def tratar_popup_selecao_inversa_e_abastecimento(self, update_callback=None, stop_event=None):
        """
        Trata o popup de Seleção Inversa com gravação passo a passo de todas as ações.
        """
        self._salvar_print_debug("01_popup_detectado", info_texto="Popup de Seleção Inversa disparado")

        if update_callback:
            update_callback({'status': 'Popup Seleção Inversa detectado! Executando correção automática...'})

        # 1. Pressiona ALT+O para fechar o 1º popup
        time.sleep(0.2)
        pyautogui.hotkey('alt', 'o')
        time.sleep(0.7)

        # 2. Verifica se o 2º popup de Atenção ainda está na tela
        tem_2o_pop, tipo_2o = self._detectar_popup_atencao()
        if tem_2o_pop:
            print(f"[MixProcessor] 2º popup detectado ({tipo_2o}). Fechando com ALT+O...")
            self._salvar_print_debug("02_segundo_popup_atencao", info_texto=f"2º popup detectado: {tipo_2o}")
            pyautogui.hotkey('alt', 'o')
            time.sleep(0.5)

        self._salvar_print_debug("02_apos_fechar_popups", info_texto="Popups fechados, prestes a clicar na aba")

        # 3. Clicar na aba Forma de Abastecimento / Logística
        coord_aba = self.coords.get('aba_forma_abastecimento_mix') or \
                    self.coords.get('aba_forma_abastecimento') or \
                    self.coords.get('aba_logis_abast_abastecimento')
        if coord_aba:
            if update_callback:
                update_callback({'status': 'Acessando aba Forma de Abastecimento...'})
            self._salvar_print_debug("03_clique_aba_abastecimento", draw_point=coord_aba, info_texto=f"Clicando na aba em {coord_aba}")
            self._click(coord_aba)
            time.sleep(1.5)
        else:
            # Tenta encontrar a aba Forma de Abastecimento via OCR
            try:
                screenshot = pyautogui.screenshot()
                screenshot_np = np.array(screenshot)
                ocr = self._get_ocr()
                if ocr:
                    res, _ = ocr(screenshot_np)
                    if res:
                        for box, text, _ in res:
                            txt_upper = text.upper()
                            if ("FORMA" in txt_upper and "ABAST" in txt_upper) or "LOGIS" in txt_upper:
                                cx = int((box[0][0] + box[2][0]) / 2)
                                cy = int((box[0][1] + box[2][1]) / 2)
                                self._salvar_print_debug("03_clique_aba_ocr", draw_point=[cx, cy], info_texto=f"Aba encontrada via OCR: '{text}'")
                                self._click([cx, cy])
                                time.sleep(1.5)
                                break
            except Exception as e:
                print(f"[MixProcessor] Tentativa de clique na aba via OCR: {e}")

        # 4. Analisar grid "Espécie de Endereço" e ler dinamicamente a embalagem do produto (ex: CX 120, DP 60) e dimensões
        if update_callback:
            update_callback({'status': 'Lendo configuração de Pulmão/Apanha e preenchendo Seleção Inversa...'})

        dados_pulmao = {'embalagem': None, 'lastro': '100', 'altura': '50', 'est_min': '0,000'}
        coord_selecao_inversa = self.coords.get('linha_selecao_inversa_mix')
        coord_pulmao = self.coords.get('linha_pulmao_mix')

        # Realiza varredura no grid para capturar com precisão a embalagem ativa do produto
        try:
            import re
            img_grid = pyautogui.screenshot()
            img_np = np.array(img_grid)
            ocr = self._get_ocr()
            if ocr:
                res_grid, _ = ocr(img_np)
                if res_grid:
                    for it in res_grid:
                        txt = it[1].strip()
                        cy = (it[0][0][1] + it[0][2][1]) / 2.0
                        cx = (it[0][0][0] + it[0][2][0]) / 2.0
                        
                        # Faixa vertical do grid de Espécie de Endereço (y entre 670 e 750)
                        if 670 <= cy <= 750:
                            # Detecta Embalagem (CX 120, DP 60, CX 24, UN 1, etc.)
                            m_emb = re.search(r'(CX|DP|UN|FD|PCT|PC|CJ|KG|LT)\s*\.?\s*\d+', txt.upper())
                            if m_emb:
                                if dados_pulmao['embalagem'] is None or cy > 700:
                                    dados_pulmao['embalagem'] = m_emb.group(0).replace('.', '').strip()
                            
                            # Detecta Lastro na coluna de Lastro (X entre 480 e 540)
                            if 480 <= cx <= 540 and txt.isdigit() and len(txt) <= 3:
                                dados_pulmao['lastro'] = txt
                                
                            # Detecta Altura na coluna de Altura (X entre 545 e 590)
                            if 545 <= cx <= 590 and txt.isdigit() and len(txt) <= 3:
                                dados_pulmao['altura'] = txt
        except Exception as e:
            print(f"[MixProcessor] Leitura do grid de abastecimento: {e}")

        # Se nenhuma embalagem específica foi lida, fallback padrão
        if not dados_pulmao.get('embalagem'):
            dados_pulmao['embalagem'] = 'CX 120'

        # Usa estritamente a coordenada salva calibrada pelo usuário
        coord_alvo = coord_selecao_inversa or coord_pulmao

        emb = dados_pulmao.get('embalagem')
        raw_lastro = dados_pulmao.get('lastro', '100')
        lastro = raw_lastro if (raw_lastro.isdigit() and len(raw_lastro) <= 3) else '100'
        raw_altura = dados_pulmao.get('altura', '50')
        altura = raw_altura if (raw_altura.isdigit() and len(raw_altura) <= 3) else '50'
        est_min = '0,000'

        self._salvar_print_debug("04_leitura_pulmao_concluida", draw_point=coord_pulmao, info_texto=f"Dados lidos: Embalagem={emb} | Lastro={lastro} | Altura={altura} | EstMin={est_min}")

        print(f"[MixProcessor] 1º Clique: Selecionando célula de SELEÇÃO INVERSA em {coord_alvo}...")
        self._salvar_print_debug("05_prestes_clicar_embalagem_inversa", draw_point=coord_alvo, info_texto=f"1º Clique: Alvo {coord_alvo}")
        self._click(coord_alvo)
        time.sleep(0.3)

        print(f"[MixProcessor] 2º Clique: Abrindo opções de Embalagem em {coord_alvo}...")
        self._click(coord_alvo)
        time.sleep(0.3)
        self._salvar_print_debug("05_apos_clique_embalagem_inversa", draw_point=coord_alvo, info_texto="2º Clique efetuado para abrir dropdown")

        print(f"[MixProcessor] Replicando Pulmão para Seleção Inversa: Embalagem={emb} | Lastro={lastro} | Altura={altura} | EstMin={est_min}")

        # 1º Campo: Seleciona Embalagem navegando com Down no combobox e dá Tab
        self._selecionar_embalagem_combobox(coord_alvo, emb)
        pyautogui.press('tab')
        time.sleep(0.2)
        self._salvar_print_debug("06_apos_tab_embalagem", info_texto="Embalagem selecionada, foco em Lastro")

        # 2º Campo (após Tab): Limpa valor residual sugerido pelo Consinco e digita Lastro
        pyautogui.press('backspace', presses=4)
        pyautogui.press('delete', presses=4)
        time.sleep(0.05)
        pyautogui.write(str(lastro), interval=0.04)
        time.sleep(0.2)
        self._salvar_print_debug("07_apos_digitar_lastro", info_texto=f"Lastro digitado: {lastro}")
        pyautogui.press('tab')
        time.sleep(0.15)

        # 3º Campo (após Tab): Limpa e digita Altura
        pyautogui.press('backspace', presses=4)
        pyautogui.press('delete', presses=4)
        time.sleep(0.05)
        pyautogui.write(str(altura), interval=0.04)
        time.sleep(0.2)
        self._salvar_print_debug("08_apos_digitar_altura", info_texto=f"Altura digitada: {altura}")
        pyautogui.press('tab')
        time.sleep(0.15)

        # 4º Campo (após Tab): Limpa e digita Quantidade Mínima (0,000)
        pyautogui.press('backspace', presses=6)
        pyautogui.press('delete', presses=6)
        time.sleep(0.05)
        pyautogui.write(str(est_min), interval=0.04)
        time.sleep(0.2)
        self._salvar_print_debug("09_apos_digitar_estmin", info_texto=f"Est. Mínimo digitado: {est_min}")
        pyautogui.press('tab')
        time.sleep(0.3)

        # 6. Salva a operação com F4
        if update_callback:
            update_callback({'status': 'Salvando alterações da Forma de Abastecimento (F4)...'})
        self._salvar_print_debug("10_prestes_salvar_f4", info_texto="Prestes a teclar F4 para salvar")
        pyautogui.press('f4')
        time.sleep(1.5)
        self._salvar_print_debug("10_apos_salvar_f4", info_texto="F4 enviado")

        # 7. Retorna para a aba principal de mix (Empresa) para seguir para o próximo produto
        pos_empresa = self.coords.get('empresa_mix')
        if pos_empresa:
            self._salvar_print_debug("11_retornando_empresa", draw_point=pos_empresa, info_texto="Clicando em Empresa")
            self._click(pos_empresa)
            time.sleep(0.6)

        if update_callback:
            update_callback({'status': 'Seleção Inversa corrigida e salva! Avançando para o próximo produto...'})

        return True

    def _selecionar_embalagem_combobox(self, coord_cell, target_emb):
        """
        Seleciona dinamicamente a embalagem correta (ex: DP 60, CX 12, CX 24, UN 1) no combobox do grid:
        1. Abre o dropdown com Alt+Down
        2. Obrigatoriamente envia Down (para ativar o evento de seleção do Delphi)
        3. Se a embalagem desejada for a primeira, envia Up para retornar a ela já ativada.
        4. Se for outra opção, continua navegando com Down até o OCR coincidir com target_emb.
        5. NÃO tecla Enter, permitindo que o Tab subsequente avance direto para o Lastro.
        """
        def norm_txt(t):
            return "".join(c for c in str(t).upper() if c.isalnum())

        norm_target = norm_txt(target_emb)
        print(f"[MixProcessor] Buscando dinamicamente embalagem '{target_emb}' (norm: '{norm_target}') no combobox...")

        cx, cy = coord_cell[0], coord_cell[1]
        x1 = max(0, cx - 60)
        y1 = max(0, cy - 20)
        w = 180
        h = 180

        ocr = self._get_ocr()

        # Abre o dropdown via atalho do Windows/Delphi
        pyautogui.hotkey('alt', 'down')
        time.sleep(0.2)

        def verificar_item_selecionado():
            try:
                crop = pyautogui.screenshot(region=(x1, y1, w, h))
                crop_np = np.array(crop)
                crop_bgr = cv2.cvtColor(crop_np, cv2.COLOR_RGB2BGR)
                hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
                blue_mask = cv2.inRange(hsv, np.array([90, 90, 90]), np.array([135, 255, 255]))

                if ocr:
                    res, _ = ocr(crop_np)
                    if res:
                        for box, text, _ in res:
                            bx1, by1 = int(box[0][0]), int(box[0][1])
                            bx2, by2 = int(box[2][0]), int(box[2][1])
                            box_crop = blue_mask[max(0, by1):min(crop_bgr.shape[0], by2), max(0, bx1):min(crop_bgr.shape[1], bx2)]
                            mean_blue = np.mean(box_crop) if box_crop.size > 0 else 0
                            
                            t_norm = norm_txt(text)
                            # Se for o item com fundo azul de seleção ativa
                            if mean_blue > 25:
                                is_match = (t_norm == norm_target or norm_target in t_norm or t_norm in norm_target)
                                return text, is_match
            except Exception as e:
                print(f"[MixProcessor] Erro na verificação OCR do combobox: {e}")
            return None, False

        # Obrigatoriamente aciona o evento de seleção com Down
        pyautogui.press('down')
        time.sleep(0.15)
        txt_sel, is_match = verificar_item_selecionado()
        self._salvar_print_debug("05_combobox_down_1", info_texto=f"Down 1: selecionado='{txt_sel}', match={is_match}")
        if is_match:
            print(f"[MixProcessor] Embalagem '{txt_sel}' confirmada no 1º Down!")
            return

        # Se não bateu no primeiro Down, verifica se a opção correta era a primeira (no topo) com Up
        pyautogui.press('up')
        time.sleep(0.15)
        txt_sel, is_match = verificar_item_selecionado()
        self._salvar_print_debug("05_combobox_up_topo", info_texto=f"Up topo: selecionado='{txt_sel}', match={is_match}")
        if is_match:
            print(f"[MixProcessor] Embalagem '{txt_sel}' confirmada no topo da lista após Up!")
            return

        # Se não era a primeira, percorre as demais opções para baixo
        for tentativa in range(10):
            pyautogui.press('down')
            time.sleep(0.15)
            txt_sel, is_match = verificar_item_selecionado()
            self._salvar_print_debug(f"05_combobox_down_{tentativa+2}", info_texto=f"Down {tentativa+2}: selecionado='{txt_sel}', match={is_match}")
            if is_match:
                print(f"[MixProcessor] Embalagem '{txt_sel}' encontrada após {tentativa+2} passos para baixo!")
                return

        time.sleep(0.1)

    def _click(self, coord):
        """Clique preciso via pynput (anti-DPI offset). Coordenadas devem vir de pynput.Listener."""
        self._mouse.position = (coord[0], coord[1])
        time.sleep(0.02)
        self._mouse.click(PynButton.left)

    def load_coordinates(self):
        coords_path = os.path.join(self.base_dir, 'coords', 'coords.json')
        if not os.path.exists(coords_path):
            if os.path.exists('coords/coords.json'):
                coords_path = 'coords/coords.json'
            else:
                return None
        with open(coords_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _detectar_status_lojas_tela(self):
        """
        Lê a região das empresas na aba de Mix/Empresa e retorna um dicionário
        com o status atual de cada loja na tela ('A' para Ativo, 'I' para Inativo).
        Utiliza RapidOCR em lote na coluna do grid com alta precisão e velocidade.
        """
        status_tela = {}
        if not self.coords:
            return status_tela
            
        store_coords = [self.coords.get(f"loja_{st}") for st in self.store_list if self.coords.get(f"loja_{st}")]
        if not store_coords:
            return status_tela
            
        min_y = max(0, min(c[1] for c in store_coords) - 40)
        sw, sh = pyautogui.size()
        max_y = min(sh, max(c[1] for c in store_coords) + 30)
        
        try:
            screenshot = pyautogui.screenshot(region=(30, min_y, 220, max_y - min_y))
            img_np = np.array(screenshot)
            
            ocr = self._get_ocr()
            if ocr:
                res, _ = ocr(img_np)
                if res:
                    itens_lidos = []
                    for box, text, score in res:
                        y_center = min_y + (box[0][1] + box[2][1]) / 2.0
                        itens_lidos.append({'text': text.strip(), 'y': y_center, 'score': score})
                        
                    for st in self.store_list:
                        coord_loja = self.coords.get(f"loja_{st}")
                        if not coord_loja:
                            continue
                        y_ref = coord_loja[1]
                        
                        # Faixa vertical com tolerância estrita de alinhamento com a linha da loja (máx 7px, pois o espaçamento entre linhas é ~17px)
                        candidatos = [it for it in itens_lidos if abs(it['y'] - y_ref) <= 7]
                        candidatos.sort(key=lambda it: abs(it['y'] - y_ref))
                        for it in candidatos:
                            t_upper = it['text'].upper()
                            if 'INATIV' in t_upper or 'INAT' in t_upper:
                                status_tela[st] = 'I'
                                break
                            elif 'ATIV' in t_upper or 'ATV' in t_upper:
                                status_tela[st] = 'A'
                                break
        except Exception as e:
            print(f"[MixProcessor] Aviso na leitura OCR de status da tela: {e}")
            
        return status_tela

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

        # Primeiro tenta equivalência exata dos aliases normalizados
        for col, norm in normalized.items():
            if norm in alias_set:
                return col

        # Fallback por prefixo para casos de sufixo inesperado no Excel
        for col, norm in normalized.items():
            if any(norm.startswith(a) for a in alias_set):
                return col

        return None

    def _normalize_action(self, value):
        txt = str(value).strip().upper()
        if not txt or txt == 'NAN':
            return None

        compact = txt.replace(' ', '').replace('_', '').replace('-', '')
        if compact in {'A', 'ATIVO'}:
            return 'A'
        if compact in {'TI', 'TOTALMENTEINATIVO'}:
            return 'TI'
        if compact in {'I', 'INATIVO'}:
            return 'I'

        return txt

    def _parse_empresas(self, val):
        """
        Interpreta e separa múltiplos códigos de lojas em uma mesma célula.
        Suporta:
        - Listas separadas por vírgula: '12,18', '12, 18', '1, 2, 3'
        - Decimais originados pelo Excel (onde '12,18' vira float 12.18): 12.18 -> ['012', '018']
        - Ponto e vírgula, barra, pipe, 'e': '12;18', '12/18', '12 e 18'
        - Códigos únicos e inteiros: 14 -> ['014'], '14.0' -> ['014']
        - Grupos ou sentinelas: 'CD', 'TI', 'G, M', 'PP'
        - Células vazias: preserva [''] para não descartar linhas sem empresa explícita (ex: TI)
        """
        if val is None or pd.isna(val):
            return ['']

        if isinstance(val, (int, float)):
            if isinstance(val, float) and not val.is_integer():
                s_val = str(val)
                partes = s_val.split('.')
                return [p.zfill(3) if p.isdigit() else p for p in partes if p]
            else:
                return [str(int(val)).zfill(3)]

        s = str(val).strip()
        if not s or s.lower() == 'nan':
            return ['']

        # Verifica se é um número inteiro vindo como float textual (ex: '14.0', '14.00')
        try:
            f_val = float(s)
            if f_val.is_integer():
                return [str(int(f_val)).zfill(3)]
        except ValueError:
            pass

        import re
        s = re.sub(r'\s+[eE]\s+', ',', s)
        tokens = re.split(r'[,;/|\\+]+', s)

        resultado = []
        for tok in tokens:
            tok = tok.strip()
            if not tok:
                continue

            # Se o sub-token for um float decimal (ex: '12.18' gerado pelo Excel a partir de 12,18)
            try:
                f = float(tok)
                if f.is_integer():
                    resultado.append(str(int(f)).zfill(3))
                    continue
                else:
                    partes = tok.split('.')
                    for p in partes:
                        if p.isdigit():
                            resultado.append(p.zfill(3))
                        elif p:
                            resultado.append(p.upper())
                    continue
            except ValueError:
                pass

            # Se contiver espaços entre números (ex: '12 18')
            if ' ' in tok:
                sub_tokens = tok.split()
                if all(st.isdigit() for st in sub_tokens):
                    for st in sub_tokens:
                        if st:
                            resultado.append(st.zfill(3))
                    continue

            if tok.isdigit():
                resultado.append(tok.zfill(3))
            else:
                resultado.append(tok.upper())

        return resultado if resultado else ['']

    def run(self, update_callback=None, stop_event=None, pause_event=None):
        if not self.coords:
            msg = "Arquivo 'coords/coords.json' não encontrado. Calibre primeiro."
            if update_callback: update_callback({'error': msg})
            return

        # --- Início do ESC Listener (Emergência) ---
        def on_press(key):
            if key == keyboard.Key.esc:
                if stop_event: stop_event.set()
                return False # Para o listener
        
        esc_listener = keyboard.Listener(on_press=on_press)
        esc_listener.start()
        # --- Fim do ESC Listener ---

        pos_empresa = self.coords.get('empresa_mix')
        if not pos_empresa:
            msg = "Coordenada 'empresa_mix' não encontrada. Calibre o Mix."
            if update_callback: update_callback({'error': msg})
            return

        input_file = os.path.join(self.base_dir, 'bd_entrada', 'mix.xlsx')
        if not os.path.exists(input_file):
            if os.path.exists('bd_entrada/mix.xlsx'):
                input_file = 'bd_entrada/mix.xlsx'
            else:
                msg = f"Arquivo '{input_file}' não encontrado."
                if update_callback: update_callback({'error': msg})
                return

        try:
            if update_callback: update_callback({'status': "Lendo planilha..."})
            df = pd.read_excel(input_file, dtype=str)
            
            # Mapeamento robusto de colunas (novo layout e legado)
            col_empresa = self._find_column(df.columns, ['EMPRESA', 'CODIGO EMPRESA'])
            col_produto = self._find_column(df.columns, ['CODIGO PRODUTO', 'CÓDIGO PRODUTO'])
            col_status = self._find_column(df.columns, ['ACAO', 'AÇÃO', 'STATUS'])

            if not col_empresa or not col_produto or not col_status:
                cols = ", ".join([str(c) for c in df.columns])
                faltantes = []
                if not col_produto:
                    faltantes.append('CODIGO_PRODUTO')
                if not col_empresa:
                    faltantes.append('EMPRESA')
                if not col_status:
                    faltantes.append('ACAO')
                raise ValueError(
                    f"Colunas obrigatórias não encontradas: {', '.join(faltantes)}. Colunas lidas: {cols}"
                )

            _colunas_reservadas = {col_empresa, col_produto, col_status}
            col_descricao = self._find_column(df.columns, ['DESCRICAO PRODUTO', 'DESCRIÇÃO PRODUTO', 'EMPRESA : PRODUTO'])
            if not col_descricao:
                col_descricao = next((c for c in df.columns if c not in _colunas_reservadas and any(x in str(c).lower() for x in ['descri', 'produto', 'nome', ' : '])), None)

            df = df.rename(columns={col_empresa: 'Código Empresa', col_produto: 'Código Produto', col_status: 'Status'})
            if col_descricao: df = df.rename(columns={col_descricao: 'Descrição'})
            
            # Expansão robusta de múltiplas lojas (ex: '12,18', 12.18, '12;18', 'G, M')
            df['Código Empresa'] = df['Código Empresa'].apply(self._parse_empresas)
            df = df.explode('Código Empresa').reset_index(drop=True)

            df['Código Empresa'] = df['Código Empresa'].apply(lambda x: str(x).strip().replace('.0', ''))
            df['Código Empresa'] = df['Código Empresa'].apply(lambda s: s.zfill(3) if s.isdigit() else s)
            df['Status'] = df['Status'].apply(self._normalize_action)
            
            produtos = df['Código Produto'].unique()
            total_produtos = len(produtos)

            # Pré-carregamento dos templates visual (Otimizado)
            import glob
            templates_cv2 = {'ativo': [], 'inativo': []}
            for stat_name in ['ativo', 'inativo']:
                caminho_glob = os.path.join(self.base_dir, 'captura_tela', f'status_{stat_name}*.png')
                arquivos = glob.glob(caminho_glob)
                if not arquivos:
                    arquivos = glob.glob(f'captura_tela/status_{stat_name}*.png')
                for path_img in arquivos:
                    tmplt = cv2.imread(path_img)
                    if tmplt is not None: templates_cv2[stat_name].append(tmplt)
            
            tem_algum_template = len(templates_cv2['ativo']) > 0 or len(templates_cv2['inativo']) > 0
            
            # Calcular Bounding Box das lojas para o Batch Screenshot
            store_coords = []
            for st in self.store_list:
                c = self.coords.get(f"loja_{st}")
                if c: store_coords.append(c)
            
            if store_coords:
                min_y = min(c[1] for c in store_coords) - 30
                max_y = max(c[1] for c in store_coords) + 30
                h_region = max_y - min_y
                w_screen, _ = pyautogui.size()
            else:
                tem_algum_template = False # Sem coordenadas de loja, desativa visão

            if update_callback:
                update_callback({'status': 'Turbo Iniciado', 'total': total_produtos})
            
            time.sleep(2) # Espera reduzida de 5s para 2s
            
            # --- Loop Principal de Produtos ---
            for i, produto in enumerate(produtos):
                if stop_event and stop_event.is_set(): break

                # Inicializa flag de popup para cada produto
                teve_popup = False
                popup_interrompeu = False

                # Pausa removida: execução segue sempre, só para se stop_event

                prod_str = str(produto).strip().replace('.0','')
                if not prod_str or prod_str.lower() == 'nan': continue

                df_prod = df[df['Código Produto'] == produto]
                desc_str = str(df_prod.iloc[0].get('Descrição', "")) if 'Descrição' in df_prod.columns else ""

                if update_callback:
                    faltam = total_produtos - (i + 1)
                    update_callback({
                        'status': f"Proc. {prod_str}",
                        'current_index': i + 1,
                        'total': total_produtos,
                        'code': prod_str,
                        'log': f"[{i+1}/{total_produtos} | Faltam: {faltam}] {prod_str} - {desc_str}"
                    })

                # Fluxo ERP Otimizado: F2 abre busca, clica no campo Codigo, digita código, F8 confirma
                pyautogui.press('f2')
                time.sleep(1.0)  # Aguardar diálogo de busca abrir completamente
                # Clique preciso no campo Codigo (se calibrado)
                if self.coords.get('campo_codigo'):
                    self._click(self.coords['campo_codigo'])
                    time.sleep(0.1)
                print(f"[DEBUG] Vai digitar o código: {prod_str}")
                pyautogui.write(prod_str, interval=0.05)  # Intervalo entre teclas para confiabilidade no ERP
                time.sleep(0.3)
                pyautogui.press('f8')
                time.sleep(1.2) # Reduzido de 2s para o F8

                # --- DEBUG: Captura tela antes de salvar produto 4766 na empresa 902 ---
                debug_monitorar = False
                if prod_str == "4766" and '902' in status_map:
                    debug_monitorar = True
                    try:
                        screenshot = pyautogui.screenshot()
                        screenshot.save('captura_tela/debug_4766_antes_salvar.png')
                        print("[DEBUG] Screenshot antes de salvar produto 4766 capturada.")
                    except Exception as e:
                        print(f"[DEBUG] Falha ao capturar screenshot antes do salvar: {e}")
                
                # (Detecção de família movida para DEPOIS do F4 — linha de salvar produto)
                
                self._click(pos_empresa)
                time.sleep(0.5) # Reduzido de 1s

                # Detecção ultra-rápida do status atual de todas as lojas na tela
                status_tela = self._detectar_status_lojas_tela()

                # Mapa de Lojas
                status_map = {str(rb['Código Empresa']).strip().upper().replace('.0', ''): str(rb.get('Status', 'I')).strip().upper() for _, rb in df_prod.iterrows()}
                cd_status = status_map.get("CD")
                
                # Regras de Agrupamento
                tem_ti_explicito = any(v == "TI" for k, v in status_map.items() if str(k).strip())
                ti_total = cd_status == "TI" or tem_ti_explicito
                ti_lojas_only = status_map.get("") == "TI" and not ti_total
                
                tem_tc = "TC" in status_map.values() or cd_status == "TC"
                tem_ta = "TA" in status_map.values() or cd_status == "TA"
                
                # Detecção Dinâmica de Grupos G, M, P baseada na Coluna Loja + Status
                group_status_map = {}
                for code, action in status_map.items():
                    code_up = str(code).upper()
                    if 'G' in code_up: group_status_map['G'] = action
                    if 'M' in code_up: group_status_map['M'] = action
                    if 'P' in code_up: group_status_map['P'] = action
                
                lojas_forcar_inativo = ["009", "010", "020", "021", "022", "023","050", "900", "901", "902"]
                lista_cds = ["015", "016", "050"]
                # Grupos de lojas
                grupos_lojas = {
                    'PP': ["001"],
                    'P': ["004", "005", "007"],
                    'M': ["008", "013", "014"],
                    'G': ["002", "006", "011", "012", "017", "018"],
                    'GG': ["003"]
                }
                # Lista fixa das 14 lojas de venda
                lojas_venda_fixas = [loja for grupo in grupos_lojas.values() for loja in grupo]
                # Monta o mapa de status das lojas de venda para o produto
                lojas_venda_status = {loja: status_map.get(loja) for loja in lojas_venda_fixas}
                # Só considera todas inativas se todas as 14 lojas estão presentes E todas com 'I'
                todas_lojas_venda_inativas = all(
                    (lojas_venda_status[loja] == 'I') for loja in lojas_venda_fixas
                )

                # --- REGRA DE ESCALONAMENTO PARA INATIVAÇÃO DOS GRUPOS (SUSPENSA TEMPORARIAMENTE) ---
                # # 1. Apura status de cada grupo
                # status_grupos = {}
                # for grupo, lojas in grupos_lojas.items():
                #     status_set = set()
                #     for loja in lojas:
                #         st = status_map.get(loja)
                #         if st:
                #             status_set.add(st)
                #     # Prioridade: se houver "A", prevalece sobre "I"
                #     if "A" in status_set:
                #         status_grupos[grupo] = "A"
                #     elif "I" in status_set and len(status_set) > 0:
                #         status_grupos[grupo] = "I"
                #     else:
                #         status_grupos[grupo] = None
                # 
                # # 2. Escalonamento de inativação
                # # Se GG=I então G, M, P também = I (PP isolado)
                # if status_grupos.get('GG') == 'I':
                #     for grupo in ['GG', 'G', 'M', 'P']:
                #         for loja in grupos_lojas[grupo]:
                #             status_map[loja] = 'I'
                # # Se G=I então M,P=I
                # elif status_grupos.get('G') == 'I':
                #     for grupo in ['M', 'P']:
                #         for loja in grupos_lojas[grupo]:
                #             status_map[loja] = 'I'
                # # Se M=I então P=I
                # elif status_grupos.get('M') == 'I':
                #     for loja in grupos_lojas['P']:
                #         status_map[loja] = 'I'
                # 
                # # 3. Após escalonamento, aplica status dominante dentro de cada grupo (exceto PP)
                # for grupo, lojas in grupos_lojas.items():
                #     if grupo == 'PP':
                #         continue  # PP é isolada
                #     status_set = set()
                #     for loja in lojas:
                #         st = status_map.get(loja)
                #         if st:
                #             status_set.add(st)
                #     if status_set:
                #         if "A" in status_set:
                #             status_final = "A"
                #         elif "I" in status_set:
                #             status_final = "I"
                #         else:
                #             status_final = list(status_set)[0]
                #         for loja in lojas:
                #             status_map[loja] = status_final

                lojas_grandes = ["002", "003", "006", "011", "012", "017", "018"]
                lojas_medias = ["008", "013", "014"]
                lojas_pequenas = ["004", "005", "007"]

                # --- BATCH SCREENSHOT (O SEGREDO DA VELOCIDADE) ---
                tela_bgr = None
                if tem_algum_template:
                    try:
                        tela_pil = pyautogui.screenshot(region=(0, min_y, w_screen, h_region))
                        tela_bgr = cv2.cvtColor(np.array(tela_pil), cv2.COLOR_RGB2BGR)
                    except: pass
                
                # Verificador de Exclusividade CD 15
                cd15_status = next((v for k, v in status_map.items() if k.lstrip('0') == '15'), None)
                cd15_ativo = (cd15_status == "A")

                # --- Loop de Lojas ---
                for loja_str in self.store_list:
                    if stop_event and stop_event.is_set(): break
                    
                    status = None
                    # Busca inteligente de status (independente de zeros à esquerda)
                    loja_num = loja_str.lstrip('0')
                    # Localiza na planilha o status da loja, independente da formatação original (ex: '15' vs '015')
                    st_planilha = next((v for k, v in status_map.items() if k.lstrip('0') == loja_num), None)
                    
                    if st_planilha and st_planilha in ["A", "I"]:
                        status = st_planilha
                    
                    # REGRA DE OURO: Se CD 15 Ativo, forçar Inativo nos CDs 16 e 50
                    if cd15_ativo and (loja_str == "016" or loja_str == "050"):
                        status = "I"
                    
                    # Regra de Grupos G, M, P (Prioridade caso não haja status direto na loja)
                    if status is None:
                        if loja_str in lojas_grandes and 'G' in group_status_map:
                            status = group_status_map['G']
                        elif loja_str in lojas_medias and 'M' in group_status_map:
                            status = group_status_map['M']
                        elif loja_str in lojas_pequenas and 'P' in group_status_map:
                            status = group_status_map['P']
                    
                    if status is not None:
                        if status not in ["A", "I"]: continue # Ignora status que não sejam A ou I
                    elif ti_total:
                        status = "I"
                    elif ti_lojas_only:
                        if loja_str in lista_cds: continue
                        status = "I"
                    elif tem_tc: status = "A" if (loja_str == "015" or (loja_str not in lojas_forcar_inativo and loja_str not in lista_cds)) else "I"
                    elif tem_ta:
                        if loja_str in lista_cds: continue
                        status = "A" if (loja_str != "001" and loja_str not in lojas_forcar_inativo) else "I"
                    elif todas_lojas_venda_inativas and loja_str in lista_cds:
                        status = "I"  # todas lojas de venda com I → inativar CDs também
                    elif cd_status and loja_str in lista_cds: status = "A" if cd_status == "A" else "I"
                    elif loja_str in lojas_forcar_inativo: status = "I"
                    else: continue

                    # Se a loja veio EXPLICITAMENTE da planilha, NUNCA pula por detecção visual (garante 100% de execução para a loja pedida)
                    vem_da_planilha = (st_planilha is not None)

                    if not vem_da_planilha:
                        # 1. VERIFICAÇÃO PRIMÁRIA VIA OCR: Se a loja automática já está no status desejado na tela, PULA!
                        # Evita alterar/inativar empresas fantasmas (009, 010, 020, 021, 022, 023, 050, 900, 901, 902)
                        if status_tela.get(loja_str) == status:
                            continue

                        # 2. Fallback visual de Template Matching se o OCR não detectou esta loja específica
                        if tela_bgr is not None and loja_str not in status_tela:
                            try:
                                coord_loja = self.coords[f"loja_{loja_str}"]
                                local_y = coord_loja[1] - min_y
                                slice_y1 = max(0, local_y - 7)
                                slice_y2 = min(h_region, local_y + 7)
                                fatia = tela_bgr[slice_y1:slice_y2, :]
                                
                                maior_c = 0; mel_est = None
                                for st_n, t_list in templates_cv2.items():
                                    for t in t_list:
                                        res = cv2.matchTemplate(fatia, t, cv2.TM_CCOEFF_NORMED)
                                        _, mx, _, _ = cv2.minMaxLoc(res)
                                        if mx > maior_c: maior_c = mx; mel_est = "A" if st_n == "ativo" else "I"
                                
                                if maior_c >= 0.85 and mel_est == status: 
                                    continue # PULA! Já está correto.
                            except: pass
                    
                    # Mecânica de Clique via pynput (Regra 65 anti-DPI)
                    self._click(self.coords[f"loja_{loja_str}"])
                    time.sleep(0.04) # Intervalo seguro para o Delphi focar a célula
                    pyautogui.press('a' if status == "A" else 'i', presses=2, interval=0.03)
                    time.sleep(0.02)

                # --- Registro Visual para Trava de Imagem (Anti-Aba Fantasma) ---
                tela_valida_gray = None
                sw, sh = pyautogui.size()
                try:
                    # Captura o topo da tela onde nascem abas e botões diferentes
                    tela_base = pyautogui.screenshot(region=(0, 0, sw, int(sh * 0.65)))
                    tela_valida_gray = cv2.cvtColor(np.array(tela_base), cv2.COLOR_RGB2GRAY)
                except:
                    pass

                # Salvar Produto
                pyautogui.press('f4')
                time.sleep(0.8)
                
                # Detecção e Tratamento Automatizado do Popup de Seleção Inversa / Atenção Consinco
                tem_popup, tipo_popup = self._detectar_popup_atencao()
                if tem_popup:
                    print(f"[MixProcessor] Popup detectado ({tipo_popup})! Executando tratamento de Seleção Inversa e Forma de Abastecimento...")
                    self.tratar_popup_selecao_inversa_e_abastecimento(update_callback=update_callback, stop_event=stop_event)
                    time.sleep(0.8)
                else:
                    time.sleep(0.4)

            pyautogui.press('f2')
            if update_callback: update_callback({'status': 'Concluído', 'finished': True})

        except Exception as e:
            if update_callback: update_callback({'error': str(e)})
        finally:
            esc_listener.stop()

def main():
    processor = MixProcessor()
    confirm = input("Mix Turbo - Pressione 's' para iniciar (ESC para parar): ")
    if confirm.lower() == 's':
        processor.run()

if __name__ == "__main__":
    main()