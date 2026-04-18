import pandas as pd
import pyautogui
import time
import os
import json
import cv2
import numpy as np
from pynput import keyboard

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02 # Reduzido para velocidade turbo

class MixProcessor:
    def __init__(self):
        self.coords = self.load_coordinates()
        self.store_list = [
            "001", "002", "003", "004", "005", "006", "007", "008", 
            "009", "010", "011", "012", "013", "014", "015", "016", 
            "017", "018", "020", "021", "022", "023", "050", "900", 
            "901", "902"
        ]

    def load_coordinates(self):
        if not os.path.exists('coords/coords.json'):
            return None
        with open('coords/coords.json', 'r') as f:
            return json.load(f)

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
            
            # Mapeamento robusto de colunas
            col_empresa = next((c for c in df.columns if str(c).startswith('Código Empresa')), 'Código Empresa')
            col_produto = next((c for c in df.columns if str(c).startswith('Código Produto')), 'Código Produto')
            col_status = next((c for c in df.columns if str(c).startswith('Status')), 'Status')
            col_descricao = next((c for c in df.columns if any(x in str(c).lower() for x in ['descri', 'produto', 'nome'])), None)

            df = df.rename(columns={col_empresa: 'Código Empresa', col_produto: 'Código Produto', col_status: 'Status'})
            if col_descricao: df = df.rename(columns={col_descricao: 'Descrição'})
            
            df['Código Empresa'] = df['Código Empresa'].apply(lambda x: str(x).strip().replace('.0', ''))
            df['Código Empresa'] = df['Código Empresa'].apply(lambda s: s.zfill(3) if s.isdigit() else s)
            
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
                
                # Check Pausa
                if pause_event and pause_event.is_set():
                    while pause_event.is_set() and not stop_event.is_set(): time.sleep(0.5)

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

                # Fluxo ERP Otimizado
                pyautogui.press('f2')
                time.sleep(0.5) # Reduzido de 1s
                pyautogui.write(prod_str)
                time.sleep(0.2) # Reduzido de 0.5s
                pyautogui.press('f8')
                time.sleep(1.2) # Reduzido de 2s para o F8
                pyautogui.click(pos_empresa)
                time.sleep(0.5) # Reduzido de 1s

                # Mapa de Lojas
                status_map = {str(rb['Código Empresa']).strip().upper().replace('.0', ''): str(rb.get('Status', 'I')).strip().upper() for _, rb in df_prod.iterrows()}
                cd_status = status_map.get("CD")
                
                # Regras de Agrupamento
                ti_total = status_map.get("CD") == "TI"
                ti_lojas_only = status_map.get("") == "TI"
                
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
                    
                    # Mecânica de Clique (Fallback)
                    pyautogui.click(self.coords[f"loja_{loja_str}"])
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
                
                # Lidar com popup de Atenção
                teve_popup = False
                try:
                    import pygetwindow as gw
                    atn = [w for w in gw.getWindowsWithTitle("Atenção") if w.visible]
                    if atn: 
                        teve_popup = True
                        pyautogui.press('s')
                        time.sleep(1.2)  # Tempo maior para garantir que as novas abas caguem a tela, se existirem
                except: pass
                
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
