import pandas as pd
import pyautogui
import time
import os
import json
import cv2
import numpy as np

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

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
            msg = "Arquivo 'coords/coords.json' não encontrado. Calibre primeiro as posições do Mix."
            if update_callback: update_callback({'error': msg})
            else: print(msg)
            return

        # Validar as coordenadas mínimas
        if 'empresa_mix' not in self.coords or not self.coords['empresa_mix']:
            msg = "Coordenada 'Empresa' não foi mapeada. Faça a calibração do Mix."
            if update_callback: update_callback({'error': msg})
            else: print(msg)
            return

        pos_empresa = self.coords['empresa_mix']
        
        # Validar se temos as lojas mapeadas
        missing_stores = [st for st in self.store_list if f"loja_{st}" not in self.coords or not self.coords[f"loja_{st}"]]
        if missing_stores:
            msg = f"As seguintes lojas não foram mapeadas na calibração: {', '.join(missing_stores)}.\nPor favor, calibre todas as 26 lojas."
            if update_callback: update_callback({'error': msg})
            else: print(msg)
            return

        input_file = 'bd_entrada/mix.xlsx'
        
        if not os.path.exists(input_file):
            msg = f"Arquivo '{input_file}' não encontrado."
            if update_callback: update_callback({'error': msg})
            else: print(msg)
            return

        try:
            if update_callback: update_callback({'status': f"Lendo dados de {input_file}..."})
            df = pd.read_excel(input_file, dtype=str)
            
            # Garantir colunas necessárias
            # Melhoria de Robustez: Buscar colunas que começam com o nome esperado (ignora sufixos como Código Empresa885)
            col_empresa = next((c for c in df.columns if str(c).startswith('Código Empresa')), 'Código Empresa')
            col_produto = next((c for c in df.columns if str(c).startswith('Código Produto')), 'Código Produto')
            col_status = next((c for c in df.columns if str(c).startswith('Status')), 'Status')
            col_descricao = next((c for c in df.columns if 'descri' in str(c).lower()), None)

            required_cols = [col_produto, col_empresa, col_status]
            for col in required_cols:
                if col not in df.columns:
                    msg = f"A coluna '{col}' (ou similar) não foi encontrada em {input_file}. Colunas atuais: {df.columns.tolist()}"
                    if update_callback: update_callback({'error': msg})
                    else: print(msg)
                    return
            
            # Renomear para padrão do script para facilitar uso posterior
            rename_dict = {col_empresa: 'Código Empresa', col_produto: 'Código Produto', col_status: 'Status'}
            if col_descricao:
                rename_dict[col_descricao] = 'Descrição'
                
            df = df.rename(columns=rename_dict)

            # Limpar e Padronizar código da loja no DF (não dar zfill em textos como 'CD')
            df['Código Empresa'] = df['Código Empresa'].apply(lambda x: str(x).strip().replace('.0', ''))
            
            # Agrupar por produto
            produtos = df['Código Produto'].unique()
            total_produtos = len(produtos)

            if total_produtos == 0:
                msg = "Nenhum produto encontrado na planilha."
                if update_callback: update_callback({'error': msg})
                else: print(msg)
                return

            if update_callback:
                update_callback({'status': 'Iniciando Manutenção...', 'total': total_produtos})
                
            # Pré-carregamento dos templates (se existirem) na memória 1 única vez para performance letal
            import glob
            templates_cv2 = {'ativo': [], 'inativo': []}
            for stat_name in ['ativo', 'inativo']:
                # Puxa qualquer arquivo que comece com status_ativo... ou status_inativo...
                arquivos = glob.glob(f'captura_tela/status_{stat_name}*.png')
                for path_img in arquivos:
                    tmplt = cv2.imread(path_img)
                    if tmplt is not None:
                        templates_cv2[stat_name].append(tmplt)
            
            tem_algum_template = len(templates_cv2['ativo']) > 0 or len(templates_cv2['inativo']) > 0
            
            if not tem_algum_template and update_callback:
                update_callback({'log': 'DICA: Adicione "status_ativo.png" e "status_inativo.png" na pasta "captura_tela" para pular lojas já processadas e dobrar a velocidade do robô!'})
            
            if not update_callback: 
                print("Iniciando em 5 segundos... Mude para o navegador/sistema!")
                time.sleep(5)
            else:
                time.sleep(2)
            
            if stop_event and stop_event.is_set(): return

            produtos_processados = 0

            for produto in produtos:
                if stop_event and stop_event.is_set():
                    if update_callback:
                        update_callback({'status': 'Parado pelo usuário.', 'finished': True})
                    return

                if pause_event and pause_event.is_set():
                    if update_callback: update_callback({'status': 'PAUSADO'})
                    while pause_event.is_set():
                        if stop_event and stop_event.is_set(): return
                        time.sleep(0.5)
                    if update_callback: update_callback({'status': 'Processando'})

                prod_str = str(produto).strip().replace('.0','')
                if not prod_str or prod_str.lower() == 'nan':
                    continue

                # Filtrar o dataframe para pegar as configurações apenas desse produto
                df_prod = df[df['Código Produto'] == produto]

                # Obter a descrição do produto se existir
                desc_str = ""
                if 'Descrição' in df.columns and not df_prod.empty:
                    desc_val = df_prod.iloc[0]['Descrição']
                    if pd.notna(desc_val):
                        desc_str = f" - {str(desc_val).strip()}"

                faltam = total_produtos - (produtos_processados + 1)

                if update_callback:
                    update_callback({
                        'status': f"Processando Produto {prod_str}",
                        'current_index': produtos_processados + 1,
                        'total': total_produtos,
                        'code': prod_str,
                        'log': f"Item {produtos_processados+1}/{total_produtos} (Faltam {faltam}): Produto {prod_str}{desc_str}"
                    })

                # Fluxo na tela do ERP
                time.sleep(5) # "na tela ativa após uma contagem de 5 segundos..."
                pyautogui.press('f2')
                time.sleep(1)
                
                pyautogui.write(prod_str)
                time.sleep(0.5)
                
                pyautogui.press('f8')
                time.sleep(2) # Respiro para a busca carregar

                # Clicar em Empresa
                pyautogui.click(pos_empresa)
                time.sleep(1)

                # Criar um dicionário de loja -> Status para busca rápida
                # Se houver duplicidade, mantém o último status para aquela loja naquele produto
                status_map = dict()
                cd_status = None # Para registrar se existe alguma instrução genérica "CD"
                
                for _, rb in df_prod.iterrows():
                    empresa_val = str(rb['Código Empresa']).strip().upper().replace('.0', '')
                    status_val = str(rb.get('Status', 'I')).strip().upper()
                    
                    if empresa_val == "CD":
                        cd_status = status_val
                    else:
                        st_code = empresa_val.zfill(3)
                        status_map[st_code] = status_val

                # Lista de lojas que DEVEM ser inativadas sempre, mesmo se não estiverem na planilha
                lojas_forcar_inativo = ["009", "010", "020", "021", "022", "023","050", "900", "901", "902"]
                
                # Lista de CDs
                lista_cds = ["015", "016", "050"]

                # Loop nas lojas
                for loja_str in self.store_list:
                    if stop_event and stop_event.is_set(): return
                    
                    # Decidimos se vamos interagir com esta loja ou pular ela
                    status = None
                    
                    # Verifica regras de agrupamento dinâmico (inclusive os definidos por trat.py)
                    tem_ti = "TI" in status_map.values() or cd_status == "TI"
                    tem_tc = "TC" in status_map.values() or cd_status == "TC"
                    tem_ta = "TA" in status_map.values() or cd_status == "TA"
                    tem_tip = "TIP" in status_map.values() 
                    tem_tim = "TIM" in status_map.values()
                    
                    lojas_pequenas = ["004", "005", "007", "008", "014"]
                    lojas_medias = ["012", "013", "018"]
                    lojas_grandes = ["002", "003", "006", "011", "017"]

                    # As marcações explícitas de planilha priorizam sobre os agrupamentos gerais TIM/TIP/TA/TI
                    if loja_str in status_map and status_map[loja_str] in ["A", "I"]:
                        status = status_map[loja_str]
                    elif tem_ti:
                        status = "I"
                    elif tem_tc:
                        # TC (Todos Centralizados): Apenas ativa no CD e desativa tudo.
                        status = "A" if (loja_str == "015" or (loja_str not in lojas_forcar_inativo and loja_str not in lista_cds)) else "I"
                    elif tem_ta:
                        if loja_str in lista_cds:
                            continue # Para não mexer nos CDs se não paramerizado explicitamente
                        status = "A" if (loja_str != "001" and loja_str not in lojas_forcar_inativo) else "I"
                    elif tem_tip:
                        if loja_str in lojas_forcar_inativo:
                            status = "I"
                        elif loja_str in lista_cds:
                            continue # Para não mexer nos CDs se não paramerizado
                        elif loja_str in lojas_pequenas:
                            status = "I"
                        elif loja_str in lojas_medias or loja_str in lojas_grandes:
                            status = "A"
                        else:
                            status = "I"
                    elif tem_tim:
                        if loja_str in lojas_forcar_inativo:
                            status = "I"
                        elif loja_str in lista_cds:
                            continue # Para não mexer nos CDs se não paramerizado
                        elif loja_str in lojas_grandes:
                            status = "A"
                        else:
                            status = "I"
                    elif cd_status and loja_str in lista_cds:
                        status = "A" if cd_status == "A" else "I"
                    elif loja_str in lojas_forcar_inativo:
                        status = "I"
                    else:
                        # Se não está na planilha, não é CD (com regra ativa) e não é grupo forçado, pula.
                        continue
                    
                    coord_loja = self.coords[f"loja_{loja_str}"]
                    x_loja, y_loja = coord_loja
                    
                    # CÉREBRO VISUAL: Leitura inteligente da "fatia" horizontal da tela no Eixo Y
                    estado_tela = None
                    if 'tem_algum_template' in locals() and tem_algum_template:
                        try:
                            # 1. Encontra a maior altura entre todas as fotos da pasta para evitar crash do OpenCV 
                            # (caso a imagem do usuário seja maior que a fatia delimitada)
                            max_h = 20
                            for _, lista in templates_cv2.items():
                                for t in lista:
                                    if t is not None and t.shape[0] > max_h:
                                        max_h = t.shape[0]
                                        
                            w_screen, _ = pyautogui.size()
                            slice_h = max_h + 10 # Dá uma margem de folga 
                            f_y = max(0, int(y_loja - (slice_h / 2)))
                            
                            tela_pil = pyautogui.screenshot(region=(0, f_y, w_screen, slice_h))
                            tela_bgr = cv2.cvtColor(np.array(tela_pil), cv2.COLOR_RGB2BGR)
                            
                            maior_confianca = 0
                            melhor_estado = None
                            
                            # 2. Match OpenCV com todas as etiquetas (Multi-Scale 0.9x a 1.1x)
                            escalas = [1.0, 0.9, 1.1]
                            for stat_name, lista_templates in templates_cv2.items():
                                for tmplt in lista_templates:
                                    for sc in escalas:
                                        # Redimensiona o template para bater com o DPI/Resolução da tela do usuário
                                        w_t = int(tmplt.shape[1] * sc)
                                        h_t = int(tmplt.shape[0] * sc)
                                        
                                        if w_t > tela_bgr.shape[1] or h_t > tela_bgr.shape[0]:
                                            continue
                                            
                                        tmplt_res = cv2.resize(tmplt, (w_t, h_t), interpolation=cv2.INTER_AREA)
                                        res = cv2.matchTemplate(tela_bgr, tmplt_res, cv2.TM_CCOEFF_NORMED)
                                        _, max_val, _, _ = cv2.minMaxLoc(res)
                                        
                                        if max_val > maior_confianca:
                                            maior_confianca = max_val
                                            melhor_estado = stat_name
                                        
                            if maior_confianca >= 0.70: # 70% segura variações fortes do ClearType das fontes
                                estado_tela = "A" if melhor_estado == "ativo" else "I"
                            else:
                                if update_callback: update_callback({'log': f"[Visão] Loja {loja_str}: Baixa confiança de leitura ({maior_confianca*100:.1f}%). Executando por segurança."})
                        except Exception as e:
                            if update_callback: update_callback({'log': f"[CRÍTICO] A Visão falhou as texturas. Erro OpenCV: {e}"})
                            pass
                            
                    # 3. Pula se a tela já estiver exatamente como o GAM ia digitar
                    if estado_tela == status:
                        if update_callback: 
                            status_print = "Ativo" if status == "A" else "Inativo"
                            update_callback({'log': f"Loja {loja_str}: Já estava {status_print} visualmente. Economizou! Pulando..."})
                        continue

                    # 4. Caso contário, precisa agir mecanicamente
                    pyautogui.click(coord_loja) # Clica na loja
                    time.sleep(0.1) # Reduzido de 0.5 para 0.1 devido ao PAUSE global

                    if status == "A":
                        # Ativar
                        pyautogui.press('a', presses=2, interval=0.05)
                    else:
                        # Inativar
                        pyautogui.press('i', presses=2, interval=0.05)
                        
                    time.sleep(0.1)

                # Finaliza edição do produto atual
                pyautogui.press('f4')
                time.sleep(0.8) # Tempo curto para o popup aparecer, se houver
                
                # Lidar com possível popup "Atenção" (Caracteres Especiais) acionado pelo F4
                try:
                    import pygetwindow as gw
                    active_window = gw.getActiveWindow()
                    if active_window and "Atenção" in active_window.title:
                        pyautogui.press('s') # Sim
                        time.sleep(0.5)
                except Exception:
                    pass
                
                time.sleep(1) # Tempo final pra salvar e liberar F2 novamente
                produtos_processados += 1

            # Finalizou todos
            time.sleep(1)
            pyautogui.press('f10')
            
            final_msg = "Manutenção de Mix finalizada para todos os itens."
            if update_callback:
                update_callback({'status': 'Concluído', 'finished': True, 'log': final_msg})
            else:
                print(f"\n=== {final_msg} ===")
                pyautogui.alert(final_msg)

        except Exception as e:
            err = f"Erro inesperado no Mix: {e}"
            if update_callback: update_callback({'error': err})
            else: print(err)

def main():
    processor = MixProcessor()
    
    print("=== Robô de Mix Ativo ===")
    if not processor.coords:
        print("Calibre as posições primeiro.")
        return

    confirm = input("Digite 's' para iniciar ou 'n' para sair: ")
    if confirm.lower() != 's':
        return

    try:
        processor.run()
    finally:
         input("\nPressione Enter para fechar...")

if __name__ == "__main__":
    main()
