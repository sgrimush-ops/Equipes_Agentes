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

class MixProcessor:
    def __init__(self):
        self.coords = self.load_coordinates()
        self.familia_cleaner = FamiliaDescriptionCleaner()
        self._mouse = PynMouse()  # Cliques via pynput para paridade DPI (Regra 65)
        self.store_list = [
            "001", "002", "003", "004", "005", "006", "007", "008", 
            "009", "010", "011", "012", "013", "014", "015", "016", 
            "017", "018", "020", "021", "022", "023", "050", "900", 
            "901", "902"
        ]

    def _click(self, coord):
        """Clique preciso via pynput (anti-DPI offset). Coordenadas devem vir de pynput.Listener."""
        self._mouse.position = (coord[0], coord[1])
        time.sleep(0.02)
        self._mouse.click(PynButton.left)

    def load_coordinates(self):
        if not os.path.exists('coords/coords.json'):
            return None
        with open('coords/coords.json', 'r') as f:
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

        input_file = 'bd_entrada/mix.xlsx'
        if not os.path.exists(input_file):
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
            
            df['Código Empresa'] = df['Código Empresa'].apply(lambda x: str(x).strip().replace('.0', ''))
            df['Código Empresa'] = df['Código Empresa'].apply(lambda s: s.zfill(3) if s.isdigit() else s)
            df['Status'] = df['Status'].apply(self._normalize_action)
            
            produtos = df['Código Produto'].unique()
            total_produtos = len(produtos)

            # Pré-carregamento dos templates visual (Otimizado)
            import glob
            templates_cv2 = {'ativo': [], 'inativo': []}
            for stat_name in ['ativo', 'inativo']:
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
                
                lojas_forcar_inativo = ["009", "010", "016" ] #"020", "021", "022", "023","050", "900", "901", "902"]
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

                # --- REGRA DE ESCALONAMENTO PARA INATIVAÇÃO DOS GRUPOS ---
                # 1. Apura status de cada grupo
                status_grupos = {}
                for grupo, lojas in grupos_lojas.items():
                    status_set = set()
                    for loja in lojas:
                        st = status_map.get(loja)
                        if st:
                            status_set.add(st)
                    # Prioridade: se houver "A", prevalece sobre "I"
                    if "A" in status_set:
                        status_grupos[grupo] = "A"
                    elif "I" in status_set and len(status_set) > 0:
                        status_grupos[grupo] = "I"
                    else:
                        status_grupos[grupo] = None

                # 2. Escalonamento de inativação
                # Se GG=I então G, M, P também = I (PP isolado)
                if status_grupos.get('GG') == 'I':
                    for grupo in ['GG', 'G', 'M', 'P']:
                        for loja in grupos_lojas[grupo]:
                            status_map[loja] = 'I'
                # Se G=I então M,P=I
                elif status_grupos.get('G') == 'I':
                    for grupo in ['M', 'P']:
                        for loja in grupos_lojas[grupo]:
                            status_map[loja] = 'I'
                # Se M=I então P=I
                elif status_grupos.get('M') == 'I':
                    for loja in grupos_lojas['P']:
                        status_map[loja] = 'I'

                # 3. Após escalonamento, aplica status dominante dentro de cada grupo (exceto PP)
                for grupo, lojas in grupos_lojas.items():
                    if grupo == 'PP':
                        continue  # PP é isolada
                    status_set = set()
                    for loja in lojas:
                        st = status_map.get(loja)
                        if st:
                            status_set.add(st)
                    if status_set:
                        if "A" in status_set:
                            status_final = "A"
                        elif "I" in status_set:
                            status_final = "I"
                        else:
                            status_final = list(status_set)[0]
                        for loja in lojas:
                            status_map[loja] = status_final

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

                    # Visão Turbo em Memória
                    if tela_bgr is not None:
                        try:
                            coord_loja = self.coords[f"loja_{loja_str}"]
                            local_y = coord_loja[1] - min_y
                            slice_y1 = max(0, local_y - 15)
                            slice_y2 = min(h_region, local_y + 15)
                            fatia = tela_bgr[slice_y1:slice_y2, :]
                            
                            maior_c = 0; mel_est = None
                            for st_n, t_list in templates_cv2.items():
                                for t in t_list:
                                    res = cv2.matchTemplate(fatia, t, cv2.TM_CCOEFF_NORMED)
                                    _, mx, _, _ = cv2.minMaxLoc(res)
                                    if mx > maior_c: maior_c = mx; mel_est = "A" if st_n == "ativo" else "I"
                            
                            if maior_c >= 0.75 and mel_est == status: 
                                continue # PULA! Já está correto.
                        except: pass
                    
                    # Mecânica de Clique via pynput (Regra 65 anti-DPI)
                    self._click(self.coords[f"loja_{loja_str}"])
                    time.sleep(0.01)
                    pyautogui.press('a' if status == "A" else 'i', presses=2, interval=0.01)

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
                # ...existing code...
                
                # Detecção visual do popup antes e depois do ALT+S
                try:
                    popup_template = cv2.imread('captura_tela/popup_consinco.png')
                    if popup_template is not None:
                        # Região central onde normalmente aparece o popup
                        px, py, pw, ph = 540, 320, 480, 100
                        screenshot_popup = pyautogui.screenshot(region=(px, py, pw, ph))
                        screenshot_popup_bgr = cv2.cvtColor(np.array(screenshot_popup), cv2.COLOR_RGB2BGR)
                        res_popup = cv2.matchTemplate(screenshot_popup_bgr, popup_template, cv2.TM_CCOEFF_NORMED)
                        _, max_val_popup, _, _ = cv2.minMaxLoc(res_popup)
                        print(f"[DEBUG] Similaridade popup Consinco: {max_val_popup:.2f}")
                        if max_val_popup >= 0.75:
                            teve_popup = True
                            print("[MixProcessor] Popup Consinco detectado! Enviando ALT+S...")
                            pyautogui.hotkey('alt', 's')
                            time.sleep(1.0)
                            # Após ALT+S, verifica se o popup sumiu
                            screenshot_popup2 = pyautogui.screenshot(region=(px, py, pw, ph))
                            screenshot_popup2_bgr = cv2.cvtColor(np.array(screenshot_popup2), cv2.COLOR_RGB2BGR)
                            res_popup2 = cv2.matchTemplate(screenshot_popup2_bgr, popup_template, cv2.TM_CCOEFF_NORMED)
                            _, max_val_popup2, _, _ = cv2.minMaxLoc(res_popup2)
                            print(f"[DEBUG] Similaridade popup Consinco após ALT+S: {max_val_popup2:.2f}")
                            if max_val_popup2 >= 0.75:
                                print("[MixProcessor] Popup Consinco NÃO sumiu após ALT+S! Parando execução imediatamente.")
                                if update_callback:
                                    update_callback({'error': "Popup Consinco não sumiu após ALT+S. Execução interrompida para evitar travamento!"})
                                if stop_event:
                                    stop_event.set()
                                print("[Gemini] Execução abortada por popup persistente!")
                                popup_interrompeu = True
                                break
                            # Após ALT+S, valida se voltou para tela de digitação do código
                            x, y, w, h = 900, 60, 160, 60  # Ajuste conforme necessário para sua resolução
                            screenshot = pyautogui.screenshot(region=(x, y, w, h))
                            screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                            template = cv2.imread('captura_tela/campo_codigo.png')
                            if template is not None:
                                res = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
                                _, max_val, _, _ = cv2.minMaxLoc(res)
                                print(f"[DEBUG] Similaridade campo 'Codigo' após ALT+S: {max_val:.2f}")
                                if max_val < 0.75:
                                    print("[MixProcessor] Campo 'Codigo' NÃO encontrado após ALT+S! Parando execução imediatamente.")
                                    if update_callback:
                                        update_callback({'error': "Campo 'Codigo' não encontrado após ALT+S. Execução interrompida para evitar travamento!"})
                                    if stop_event:
                                        stop_event.set()
                                    print("[Gemini] Execução abortada: campo 'Codigo' não voltou!")
                                    popup_interrompeu = True
                                    break
                            else:
                                print("[MixProcessor] Template campo_codigo.png não encontrado para validação visual!")
                            # Se chegou até aqui, popup foi tratado, mas para máxima segurança, interrompe o produto atual
                            print("[Gemini] Popup tratado, interrompendo processamento deste produto!")
                            popup_interrompeu = True
                            break
                    else:
                        print("[MixProcessor] Template popup_consinco.png não encontrado para detecção de popup!")
                except Exception as e:
                    print(f"Aviso: Falha na detecção/tratamento de popup Consinco: {e}")
                
                # --- TRAVA DE SEGURANÇA BASEADA EM DIFERENÇA DE IMAGEM ---
                # Agimos APENAS se houve o Popup, que é o gatilho da nova tela indesejada
                try:
                    if teve_popup and tela_valida_gray is not None:
                        tela_apos = pyautogui.screenshot(region=(0, 0, sw, int(sh * 0.65)))
                        tela_apos_gray = cv2.cvtColor(np.array(tela_apos), cv2.COLOR_RGB2GRAY)
                        
                        # Calculo de Diferença Estrutural
                        diff = cv2.absdiff(tela_valida_gray, tela_apos_gray)
                        mudanca_visual = np.mean(diff)
                        
                        # Limiar calibrado: Mudanças no Consinco (fundo e grid para Abas brutas) causam > 8 de variância 
                        if mudanca_visual > 8.0:
                            msg_trava = f"🚨 TRAVA VISUAL DE SEGURANÇA: As abas e a estrutura da tela mudaram fortemente (Delta={mudanca_visual:.1f}). Operação ABORTADA para evitar danos!"
                            if update_callback: update_callback({'error': msg_trava})
                            else: print(msg_trava)
                            
                            # Aciona parada de emergência
                            if stop_event: stop_event.set()
                            break # Encerra o laço de produtos principal
                except Exception as e:
                    print("Aviso: Falha na trava visual:", e)
                
                time.sleep(0.5)

                # Se popup interrompeu, para o loop principal imediatamente
                if popup_interrompeu:
                    print("[Gemini] Loop principal abortado por popup!")
                    break

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