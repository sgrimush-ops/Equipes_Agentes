import os
import json
import time
import pandas as pd
import threading
import tkinter as tk
from tkinter import messagebox
from pynput import mouse
import pyautogui
import cv2
import numpy as np
from actions.base_action import BaseAction



class MinMaxCalibrationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calibração - Ajuste Min/Max")
        self.geometry("400x350")
        self.resizable(False, False)
        
        self.coords_file = BaseAction.get_coords_path('coords_ajuste_min_max.json')
        # Coordinates needed for the min/max adjustment action
        self.coords = {"aba_local": None, "minimo_loja_1": None}
        self.load_existing_coords()
        
        tk.Label(self, text="Calibração do Ajuste Min/Max", font=("Segoe UI", 12, "bold")).pack(pady=10)
        tk.Label(self, text="Clique nos botões abaixo para definir as posições na tela.", wraplength=380).pack(pady=5)
        
        # Aba Local
        self.btn_aba_local = tk.Button(self, text="1. Aba Local", command=lambda: self.start_capture("aba_local"), width=30)
        self.btn_aba_local.pack(pady=5)
        self.lbl_aba_local = tk.Label(self, text="Não definido", fg="red")
        self.lbl_aba_local.pack()
        
        # Mínimo Loja 1
        self.btn_minimo_loja_1 = tk.Button(self, text="2. Mínimo Loja 1", command=lambda: self.start_capture("minimo_loja_1"), width=30)
        self.btn_minimo_loja_1.pack(pady=5)
        self.lbl_minimo_loja_1 = tk.Label(self, text="Não definido", fg="red")
        self.lbl_minimo_loja_1.pack()

        self.btn_save = tk.Button(self, text="Salvar e Fechar", command=self.save_coords, state="disabled", bg="#4CAF50", fg="white")
        self.btn_save.pack(pady=15, fill='x', padx=20)
        
        self.update_initial_view()

    def load_existing_coords(self):
        if os.path.exists(self.coords_file):
            try:
                with open(self.coords_file, 'r') as f:
                    saved = json.load(f)
                    for k in self.coords.keys():
                        if k in saved:
                            self.coords[k] = saved[k]
            except Exception:
                pass

    def update_initial_view(self):
        for key, lbl in [("aba_local", self.lbl_aba_local), ("minimo_loja_1", self.lbl_minimo_loja_1)]:
            if self.coords.get(key):
                x, y = self.coords[key]
                lbl.config(text=f"Salvo: {x}, {y}", fg="green")
        if all(self.coords.values()):
            self.btn_save.config(state="normal")

    def start_capture(self, key):
        btns = {"aba_local": self.btn_aba_local, "minimo_loja_1": self.btn_minimo_loja_1}
        btn = btns[key]
        btn.config(text="Aponte e CLIQUE", state="disabled")
        threading.Thread(target=self.capture_thread, args=(key, btn, btn.cget("text")), daemon=True).start()

    def capture_thread(self, key, btn, orig_text):
        click_x, click_y = 0, 0
        def on_click(x, y, button, pressed):
            nonlocal click_x, click_y
            if pressed and button == mouse.Button.left:
                click_x, click_y = int(x), int(y)
                return False
                
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
            
        self.coords[key] = [click_x, click_y]
        self.after(0, lambda: self.update_ui_after_capture(key, click_x, click_y, btn, orig_text))

    def update_ui_after_capture(self, key, x, y, btn, orig_text):
        labels = {"aba_local": ("1. Aba Local", self.lbl_aba_local), 
                  "minimo_loja_1": ("2. Mínimo Loja 1", self.lbl_minimo_loja_1)}
        original_title, lbl = labels[key]
        
        btn.config(text=original_title, state="normal")
        lbl.config(text=f"Capturado: {x}, {y}", fg="green")
        
        if all(self.coords.values()):
            self.btn_save.config(state="normal")

    def save_coords(self):
        with open(self.coords_file, 'w') as f:
            json.dump(self.coords, f)
        messagebox.showinfo("Sucesso", "Coordenadas salvas com sucesso!")
        self.destroy()


class AcaoAjusteMinMax(BaseAction):
    @property
    def name(self) -> str:
        return "Ajuste de Min/Max"
        
    @property
    def description(self) -> str:
        return "Ajusta os valores Mínimo e Máximo por loja baseado na planilha ajustepp.xlsx."

    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if update_callback:
            update_callback({'status': 'Iniciando', 'log': 'Lendo arquivo de dados...'})

        # File reading
        file_path = 'bd_entrada/ajustepp.xlsx'
        coords_file = BaseAction.get_coords_path('coords_ajuste_min_max.json')

        if not os.path.exists(file_path):
            if update_callback:
                update_callback({'error': f'Arquivo {file_path} não encontrado.'})
            return
            
        if not os.path.exists(coords_file):
            if update_callback:
                update_callback({'error': 'Coordenadas não calibradas.'})
            return

        with open(coords_file, 'r') as f:
            coords = json.load(f)

        try:
            # Forçando releitura do disco sem cache do sistema/pandas:
            with open(file_path, 'rb') as f:
                # Lendo as colunas conforme solicitado
                df = pd.read_excel(f, engine='openpyxl', usecols=['Código Empresa', 'Código Produto', 'Empresa : Produto', 'Quantidade Estoque Mínimo', 'Quantidade  Estoque Máximo'])
            
            # Ordenando de forma crescente
            df = df.sort_values(by=['Código Produto', 'Código Empresa'], ascending=[True, True])
            
            produtos_agrupados = df.groupby('Código Produto')
            total_produtos = len(produtos_agrupados)
            
            if update_callback:
                update_callback({'log': f'Encontrados {total_produtos} produtos para ajustar.'})
                
        except Exception as e:
            if update_callback:
                update_callback({'error': f'Erro ao ler planilha: {str(e)}'})
            return

        # Pausa inicial
        if update_callback:
            update_callback({'log': 'Aguardando 5 segundos para você trocar para a tela do sistema...'})
        time.sleep(5)

        count = 0
        aviso_detectado_anterior = False

        for codigo_produto, df_grupo in produtos_agrupados:
            if stop_event and stop_event.is_set():
                if update_callback:
                    update_callback({'log': 'Processo interrompido pelo usuário.'})
                return
            while pause_event and pause_event.is_set():
                time.sleep(0.5)

            count += 1
            descricao_produto = str(df_grupo['Empresa : Produto'].iloc[0]) if 'Empresa : Produto' in df_grupo.columns else ""
            if update_callback:
                update_callback({'status': f'Processando {count}/{total_produtos}', 'log': f'Iniciando: {int(codigo_produto)} - {descricao_produto}'})
                
            lojas_processar = df_grupo.set_index('Código Empresa').to_dict('index')

            # 2. Comando "F2", limpa a tela para digitação;
            pyautogui.press('f2')
            time.sleep(0.5)
            
            # Se o aviso foi detectado no produto anterior, o F2 pedirá mais uma confirmação para limpar
            if aviso_detectado_anterior:
                if update_callback:
                    update_callback({'log': 'Confirmando limpeza de tela após aviso (ALT+S)...'})
                pyautogui.hotkey('alt', 's')
                time.sleep(1.0) # Tempo maior para a tela de confirmação sumir
                
                aviso_detectado_anterior = False # Resetar para o próximo loop
            
            # 3. vai digitar o código do produto;
            pyautogui.write(str(int(codigo_produto)))
            time.sleep(0.3)
            
            # 4. comando "F8";
            pyautogui.press('f8')
            time.sleep(2) # Dar tempo para carregar a tela do produto
            
            # 5. mapear a aba local, para isso vamos usar um clique;
            pyautogui.click(coords['aba_local'][0], coords['aba_local'][1])
            time.sleep(0.5)
            
            # 6. mapear local para um clique para focar no minimo da loja 1;
            pyautogui.click(coords['minimo_loja_1'][0], coords['minimo_loja_1'][1])
            time.sleep(0.5)
            # Acionar down e up para garantir o registro do campo na janela
            pyautogui.press('down')
            time.sleep(0.1)
            pyautogui.press('up')
            time.sleep(0.1)
            
            # Lógica de iteração de lojas de 1 a 18
            for num_loja in range(1, 19):
                # Verificando pause/stop event constantemente
                if stop_event and stop_event.is_set(): return
                while pause_event and pause_event.is_set(): time.sleep(0.5)

                if num_loja in lojas_processar:
                    # Loja existe na planilha
                    min_val = lojas_processar[num_loja]['Quantidade Estoque Mínimo']
                    max_val = lojas_processar[num_loja]['Quantidade  Estoque Máximo']
                    
                    # Se estiver vazio (NaN) em min_val e max_val, trata a loja como ignorada
                    if pd.isna(min_val) and pd.isna(max_val):
                        if num_loja != 18:
                            pyautogui.press('down')
                        time.sleep(0.1)
                        continue

                    # Converte para inteiro preservando o 0
                    min_val = int(min_val) if not pd.isna(min_val) else ""
                    max_val = int(max_val) if not pd.isna(max_val) else ""

                    # 7. digitar o valor minimo da loja;
                    if min_val != "":
                        if update_callback:
                            update_callback({'log': f'Loja {num_loja} | Produto: {int(codigo_produto)} - {descricao_produto} | Mín/Máx: {min_val}/{max_val}'})
                        pyautogui.write(str(min_val))
                    time.sleep(0.1)
                    
                    # 8. um "tab" para ir para o próximo campo (máximo);
                    pyautogui.press('tab')
                    time.sleep(0.1)
                    
                    # 9. digitar o maximo da loja;
                    if max_val != "":
                        pyautogui.write(str(max_val))
                    time.sleep(0.1)
                    
                    # 10. shift+tab para voltar e seta baixo, para ir para o minimo da próxima loja;
                    if num_loja != 18:
                        pyautogui.hotkey('shift', 'tab')
                        time.sleep(0.2)
                        pyautogui.press('down')
                        time.sleep(0.1)
                else:
                    # Loja não existe na planilha (ou é a 9/10), focar no próximo usando seta baixo
                    if num_loja != 18:
                        pyautogui.press('down')
                    time.sleep(0.1)

            # Finalizar essa etapa com a gravação "F4"
            pyautogui.press('f4')
            time.sleep(4) # Dar tempo para processar o save

            # Verificar se ocorreu o popup de aviso após a gravação
            # Vamos tentar encontrar o aviso por até 4 segundos após o F4, 
            # já que o sistema pode demorar um pouco para renderizar o popup 
            try:
                aviso_encontrado = False
                tempo_maximo_busca = 4.0
                tempo_inicio_busca = time.time()
                # Usar raw CV2 para a busca pois PyAutoGUI apresenta falhas internas de confidence nesse ambiente
                # O teste cv2 comprovou 1.000 (100%) de precisao com a tela
                imagens_para_procurar = [
                    'captura_tela/aviso_icone.png',
                    'captura_tela/aviso_crop_nativo.png'
                ]
                
                # Precarregando imagens
                templates_cv2 = []
                for img_path in imagens_para_procurar:
                    if os.path.exists(img_path):
                        template = cv2.imread(img_path)
                        if template is not None:
                            templates_cv2.append((img_path, template))

                while not aviso_encontrado and (time.time() - tempo_inicio_busca) < tempo_maximo_busca:
                    if len(templates_cv2) > 0:
                        # Tira a foto da tela exata do momento usando pyautogui
                        # Converte a imagem PIL para o formato padrao do OpenCV (Numpy + BGR)
                        tela_pil = pyautogui.screenshot()
                        tela_bgr = cv2.cvtColor(np.array(tela_pil), cv2.COLOR_RGB2BGR)

                        for img_name, template in templates_cv2:
                            try:
                                res = cv2.matchTemplate(tela_bgr, template, cv2.TM_CCOEFF_NORMED)
                                _, max_val, _, _ = cv2.minMaxLoc(res)
                                
                                # Se a confianca da busca bater a meta de seguranca de 80% (0.8)
                                if max_val >= 0.8:
                                    aviso_encontrado = True
                                    break
                            except Exception:
                                pass
                                
                    if not aviso_encontrado:
                        time.sleep(0.5) # Aguarda meio segundo antes de tentar procurar de novo na tela

                if aviso_encontrado:
                    aviso_detectado_anterior = True
                    if update_callback:
                        update_callback({'log': 'Aviso detectado. Pressionando Enter 2x...'})
                    pyautogui.press('enter')
                    time.sleep(0.5)
                    pyautogui.press('enter')
                    time.sleep(0.5)
            except Exception:
                pass

        if update_callback:
            update_callback({'status': 'Concluído', 'finished': True, 'log': 'Todos os produtos processados com sucesso.'})

    def has_calibration(self) -> bool:
        return True
        
    def calibrate(self, parent_window):
        MinMaxCalibrationWindow(parent_window)

def get_action():
    return AcaoAjusteMinMax()
