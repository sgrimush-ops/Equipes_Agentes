import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import threading
import queue
import json
import time
import time
import pyautogui
import pandas as pd
# Import removido devido a arquivo inexistente.

def _get_coords_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'coords', 'coords.json')

class CalibrationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calibração")
        self.geometry("400x400")
        self.resizable(False, False)
        
        self.coords = {"cd_abastecedor": None, "nova_linha": None, "posicao_comprador": None}
        self.load_existing_coords()
        
        self.font_bold = ("Segoe UI", 10, "bold")
        
        tk.Label(self, text="Assistente de Calibração", font=("Segoe UI", 12, "bold")).pack(pady=10)
        tk.Label(self, text="Siga as instruções abaixo para mapear os botões.", wraplength=380).pack(pady=5)
        
        self.btn_busca = tk.Button(self, text="1. Capturar 'CD Abastecedor'", command=lambda: self.start_capture("cd_abastecedor"), width=30)
        self.btn_busca.pack(pady=10)
        
        self.lbl_busca = tk.Label(self, text="Não definido", fg="red")
        self.lbl_busca.pack()
        
        self.btn_qtd = tk.Button(self, text="2. Capturar 'Nova Linha'", command=lambda: self.start_capture("nova_linha"), width=30)
        self.btn_qtd.pack(pady=10)
        
        self.lbl_qtd = tk.Label(self, text="Não definido", fg="red")
        self.lbl_qtd.pack()
        
        self.btn_comprador = tk.Button(self, text="3. Capturar 'Posição Comprador'", command=lambda: self.start_capture("posicao_comprador"), width=30)
        self.btn_comprador.pack(pady=10)
        
        self.lbl_comprador = tk.Label(self, text="Não definido", fg="red")
        self.lbl_comprador.pack()
        
        self.btn_save = tk.Button(self, text="Salvar e Fechar", command=self.save_coords, state="disabled", bg="#4CAF50", fg="white")
        self.btn_save.pack(pady=20, fill='x', padx=20)
        
        # Atualiza a view com base no que foi carregado
        self.update_initial_view()

    def load_existing_coords(self):
        coords_path = _get_coords_path()
        if os.path.exists(coords_path):
            try:
                with open(coords_path, 'r') as f:
                    saved = json.load(f)
                    if "cd_abastecedor" in saved:
                        self.coords["cd_abastecedor"] = saved["cd_abastecedor"]
                    if "nova_linha" in saved:
                        self.coords["nova_linha"] = saved["nova_linha"]
                    if "posicao_comprador" in saved:
                        self.coords["posicao_comprador"] = saved["posicao_comprador"]
            except Exception:
                pass

    def update_initial_view(self):
        # Atualiza tela e libera save se ambos definidos
        if self.coords.get("cd_abastecedor"):
            x, y = self.coords["cd_abastecedor"]
            self.lbl_busca.config(text=f"Salvo: {x}, {y}", fg="green")
        if self.coords.get("nova_linha"):
            x, y = self.coords["nova_linha"]
            self.lbl_qtd.config(text=f"Salvo: {x}, {y}", fg="green")
        if self.coords.get("posicao_comprador"):
            x, y = self.coords["posicao_comprador"]
            self.lbl_comprador.config(text=f"Salvo: {x}, {y}", fg="green")
            
        if all(self.coords.values()):
            self.btn_save.config(state="normal")

    def start_capture(self, key):
        if key == "cd_abastecedor": btn = self.btn_busca
        elif key == "nova_linha": btn = self.btn_qtd
        else: btn = self.btn_comprador
        # Altera o botão para avisar o usuário
        btn.config(text="Aponte e dê um CLIQUE", state="disabled")
        
        # Cria uma thread separada para não travar a janela
        threading.Thread(target=self.capture_thread, args=(key, btn, btn.cget("text")), daemon=True).start()

    def capture_thread(self, key, btn, orig_text):
        from pynput import mouse
        
        click_x, click_y = 0, 0
        def on_click(x, y, button, pressed):
            nonlocal click_x, click_y
            if pressed and button == mouse.Button.left:
                click_x, click_y = int(x), int(y)
                return False # Para o listener
                
        # Inicia o listener que vai travar até o primeiro clique esquerdo
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
            
        self.coords[key] = [click_x, click_y]
        
        # Após capturar, atualiza a UI de volta para a thread principal
        self.after(0, lambda: self.update_ui_after_capture(key, click_x, click_y, btn, orig_text))

    def update_ui_after_capture(self, key, x, y, btn, orig_text):
        if key == "cd_abastecedor": default_t = "1. Capturar 'CD Abastecedor'"
        elif key == "nova_linha": default_t = "2. Capturar 'Nova Linha'"
        else: default_t = "3. Capturar 'Posição Comprador'"
        
        btn.config(text=orig_text if "Aponte" not in orig_text else default_t, state="normal")
        
        if key == "cd_abastecedor": lbl = self.lbl_busca
        elif key == "nova_linha": lbl = self.lbl_qtd
        else: lbl = self.lbl_comprador
        
        lbl.config(text=f"Capturado: {x}, {y}", fg="green")
        
        if all(self.coords.values()):
            self.btn_save.config(state="normal")

    def save_coords(self):
        coords_path = _get_coords_path()
        all_coords = {}
        if os.path.exists(coords_path):
            try:
                with open(coords_path, 'r') as f:
                    all_coords = json.load(f)
            except Exception:
                pass
                
        all_coords.update(self.coords)
        os.makedirs(os.path.dirname(coords_path), exist_ok=True)
        with open(coords_path, 'w') as f:
            json.dump(all_coords, f)
        messagebox.showinfo("Sucesso", "Coordenadas salvas com sucesso!")
        self.destroy()

class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Painel de Automação de Pedidos")
        
        # Cores e Fontes
        self.font_bold = ("Segoe UI", 10, "bold")
        self.bg_color = "#f0f0f0"
        self.root.configure(bg=self.bg_color)

        # Centralizar a janela na tela
        window_width = 450
        window_height = 450
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Variáveis de Estado
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.queue = queue.Queue()
        self.is_running = False

        # Variáveis de Interface
        self.var_status = tk.StringVar(value="Pronto")
        self.var_progresso = tk.StringVar(value="0 / 0")
        self.var_codigo = tk.StringVar(value="-")
        self.var_descricao = tk.StringVar(value="-")
        self.var_qtd = tk.StringVar(value="-")
        
        self.create_widgets()
        self.root.after(100, self.process_queue)

    def create_widgets(self):
        # Frame Principal
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')

        # Título
        lbl_title = tk.Label(main_frame, text="Controle do Robô", font=("Segoe UI", 14, "bold"), bg=self.bg_color)
        lbl_title.pack(pady=(0, 10))
        
        # Botões de Ação
        btn_frame1 = tk.Frame(main_frame, bg=self.bg_color)
        btn_frame1.pack(fill='x', pady=5)
        
        self.btn_preparar = tk.Button(btn_frame1, text="0. Preparar Dados", command=self.preparar_dados,
                                      width=20, height=2, bg="#2196F3", fg="white",
                                      font=("Segoe UI", 9, "bold"), relief="raised", cursor="hand2")
        self.btn_preparar.pack(side='top', padx=5, pady=5)

        btn_frame2 = tk.Frame(main_frame, bg=self.bg_color)
        btn_frame2.pack(fill='x', pady=5)

        self.btn_calibrar = tk.Button(btn_frame2, text="1. Calibrar Posições", command=self.open_calibration, 
                                      width=20, height=2, relief="raised", cursor="hand2")
        self.btn_calibrar.pack(side='left', padx=5)

        self.btn_iniciar = tk.Button(btn_frame2, text="2. Iniciar Pedidos", command=self.start_automation, 
                                      width=20, height=2, bg="#4CAF50", fg="white", 
                                      font=("Segoe UI", 9, "bold"), relief="raised", cursor="hand2")
        self.btn_iniciar.pack(side='right', padx=5)

        # Painel de Status
        status_frame = tk.LabelFrame(main_frame, text="Monitoramento em Tempo Real", 
                                     font=("Segoe UI", 9, "bold"), bg=self.bg_color, padx=10, pady=10)
        status_frame.pack(fill='both', expand=True, pady=20)

        # Labels de Informação
        self.create_info_row(status_frame, "Status:", self.var_status)
        self.create_info_row(status_frame, "Progresso:", self.var_progresso)
        self.create_info_row(status_frame, "Código:", self.var_codigo)
        self.create_info_row(status_frame, "Descrição:", self.var_descricao)
        self.create_info_row(status_frame, "Quantidade:", self.var_qtd)

        # Botão Parar
        self.btn_parar = tk.Button(main_frame, text="PARAR AUTOMAÇÃO", command=self.stop_automation, 
                                   bg="#FF5252", fg="white", font=("Segoe UI", 9, "bold"), 
                                   state="disabled", cursor="hand2")
        self.btn_parar.pack(fill='x', pady=5)
        
        # Botão Pausar
        self.btn_pausar = tk.Button(main_frame, text="PAUSAR", command=self.toggle_pause, 
                                   bg="#FF9800", fg="white", font=("Segoe UI", 9, "bold"), 
                                   state="disabled", cursor="hand2")
        self.btn_pausar.pack(fill='x', pady=(0, 10))
        
        # Rodapé
        tk.Label(main_frame, text="Versão 1.0 - Requer 'digitar.csv' na pasta", font=("Segoe UI", 8), bg=self.bg_color, fg="gray").pack(side="bottom")

    def create_info_row(self, parent, label_text, variable):
        frame = tk.Frame(parent, bg=self.bg_color)
        frame.pack(fill='x', pady=2)
        tk.Label(frame, text=label_text, width=12, anchor='w', font=("Segoe UI", 9, "bold"), bg=self.bg_color).pack(side='left')
        tk.Label(frame, textvariable=variable, anchor='w', bg="white", relief="sunken", padx=5).pack(side='left', fill='x', expand=True)

    def open_calibration(self):
        CalibrationWindow(self.root)

    def preparar_dados(self):
        input_file = 'ped.xlsx'
        output_file = 'digitar.csv'
        
        self.var_status.set("Preparando dados...")
        self.root.update()

        try:
            # Lê o Excel original
            df = pd.read_excel(input_file, dtype={'codigo_interno': str})
            
            # Colunas base
            base_cols = ['codigo_interno', 'descricao', 'embseparacao']
            
            for col in base_cols:
                if col not in df.columns:
                    df[col] = ''
                    
            # Identifica colunas de loja
            loja_cols = [c for c in df.columns if str(c).lower().startswith('loja')]
            
            # Filtra lojas ativas
            active_loja_cols = []
            for col in loja_cols:
                temp_num = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                if temp_num.sum() > 0:
                    active_loja_cols.append(col)
                    
            # Prepara dataframe final
            final_cols = [c for c in base_cols if c in df.columns] + active_loja_cols
            df_final = df[final_cols].copy()
            
            # Salva em CSV com separador ;
            df_final.to_csv(output_file, index=False, sep=';', encoding='utf-8')
            
            msg = f"Arquivo '{output_file}' gerado com sucesso!\n\nLojas ativas encontradas: {len(active_loja_cols)}\n({', '.join(active_loja_cols)})"
            messagebox.showinfo("Dados Preparados", msg)
            self.var_status.set("Dados Prontos!")
            
        except FileNotFoundError:
            messagebox.showerror("Erro", f"O arquivo '{input_file}' não foi encontrado.")
            self.var_status.set("Erro na preparação")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")
            self.var_status.set("Erro na preparação")

    def start_automation(self):
        if not os.path.exists('coords/coords.json'):
             if not messagebox.askyesno("Aviso", "Arquivo 'coords/coords.json' não encontrado.\nÉ provável que você precise calibrar antes.\nDeseja continuar mesmo assim?"):
                 return

        self.is_running = True
        self.stop_event.clear()
        self.pause_event.clear()
        self.update_buttons_state()
        
        # Resetar display
        self.var_status.set("Iniciando...")
        
        # Iniciar Thread
        t = threading.Thread(target=self.run_process_thread)
        t.daemon = True
        t.start()


    def stop_automation(self):
        if self.is_running:
            self.var_status.set("Parando...")
            self.stop_event.set()
            # Se estiver pausado, libera para poder parar
            if self.pause_event.is_set():
                self.pause_event.clear()

    def toggle_pause(self):
        if not self.is_running: return
        
        if self.pause_event.is_set():
            # Retomar
            self.pause_event.clear()
            self.btn_pausar.config(text="PAUSAR", bg="#FF9800")
            self.var_status.set("Retomando...")
        else:
            # Pausar
            self.pause_event.set()
            self.btn_pausar.config(text="RETOMAR", bg="#2196F3")
            self.var_status.set("Pausando...")

    def run_process_thread(self):
        processor = OrderProcessor()
        processor.run(update_callback=self.queue.put, stop_event=self.stop_event, pause_event=self.pause_event)

    def process_queue(self):
        try:
            while True:
                data = self.queue.get_nowait()
                self.handle_update(data)
                self.queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def handle_update(self, data):
        if 'error' in data:
            messagebox.showerror("Erro", data['error'])
            self.is_running = False
            self.var_status.set("Erro")
            self.update_buttons_state()
            return

        if 'status' in data:
            self.var_status.set(data['status'])

        if 'current_index' in data and 'total' in data:
            self.var_progresso.set(f"{data['current_index']} / {data['total']}")

        if 'code' in data:
            self.var_codigo.set(str(data['code']))
        
        if 'desc' in data:
            self.var_descricao.set(data['desc'])
            
        if 'qty' in data:
            self.var_qtd.set(str(data['qty']))

        if data.get('finished'):
            self.is_running = False
            self.update_buttons_state()
            if not self.stop_event.is_set():
                messagebox.showinfo("Sucesso", "Automação finalizada com sucesso!")

    def update_buttons_state(self):
        if self.is_running:
            self.btn_iniciar.config(state="disabled", bg="#cccccc")
            self.btn_preparar.config(state="disabled", bg="#cccccc")
            self.btn_calibrar.config(state="disabled")
            self.btn_parar.config(state="normal", bg="#FF5252")
            self.btn_pausar.config(state="normal", text="PAUSAR", bg="#FF9800")
        else:
            self.btn_iniciar.config(state="normal", bg="#4CAF50")
            self.btn_preparar.config(state="normal", bg="#2196F3")
            self.btn_calibrar.config(state="normal")
            self.btn_parar.config(state="disabled", bg="#cccccc")
            self.btn_pausar.config(state="disabled", bg="#cccccc", text="PAUSAR")

def main():
    root = tk.Tk()
    app = AutomationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
