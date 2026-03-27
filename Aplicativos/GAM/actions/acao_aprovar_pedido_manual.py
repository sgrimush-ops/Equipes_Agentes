import time
import os
import sys
import pyautogui
import json
import tkinter as tk
from tkinter import messagebox

# Garante que as importações da raiz funcionem
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actions.base_action import BaseAction

class AcaoAprovarPedido(BaseAction):
    @property
    def name(self) -> str:
        return "Aprovação Automática"
        
    @property
    def description(self) -> str:
        return "Aprova automaticamente o pedido manual aguardando o processamento do sistema."
        
    def has_calibration(self) -> bool:
        return True
        
    def _load_coords(self):
        coords_file = BaseAction.get_coords_path('coords.json')
        if not os.path.exists(coords_file):
            return None
            
        try:
            with open(coords_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    def execute(self, update_callback=None, stop_event=None, pause_event=None, **kwargs):
        if update_callback:
            update_callback({'status': 'Iniciando', 'total': 0})
            
        coords = self._load_coords()
        if not coords or 'btn_aprovar' not in coords or 'btn_selecionar_todos' not in coords:
            msg = "Pontos de calibração para o botão 'Aprovar' ou 'Selecionar Todos' não encontrados. Por favor, calibre a ação primeiro."
            if update_callback: update_callback({'error': msg})
            return

        def check_pause_stop():
            if stop_event and stop_event.is_set():
                if update_callback: update_callback({'status': 'Parado pelo usuário', 'finished': True})
                return True
            if pause_event and pause_event.is_set():
                if update_callback: update_callback({'status': 'Pausado...'})
                while pause_event.is_set() and not (stop_event and stop_event.is_set()):
                    time.sleep(0.5)
                if update_callback: update_callback({'status': 'Em execução...'})
            return stop_event and stop_event.is_set()

        try:
            if update_callback: update_callback({'status': 'Aguardando 10 segundos...'})
            
            # 1. Aguarda 10 segundos
            for _ in range(10):
                if check_pause_stop(): return
                time.sleep(1)

            if check_pause_stop(): return

            # 2. Teclar alt+m
            if update_callback: update_callback({'status': 'Pressionando Alt+M'})
            pyautogui.hotkey('alt', 'm')
            
            # 3. Clique no local mapeado (btn_aprovar)
            time.sleep(1.0) # pequeno delay visual para o menu abrir ou responder
            if check_pause_stop(): return
            
            if update_callback: update_callback({'status': 'Clicando no botão mapeado...'})
            pyautogui.click(coords['btn_aprovar'][0], coords['btn_aprovar'][1])
            
            # 4. Depois de 1 segundo, teclar F8
            time.sleep(1.0)
            if check_pause_stop(): return
            
            if update_callback: update_callback({'status': 'Pressionando F8...'})
            pyautogui.press('f8')
            
            # 5. Aguardar 3 segundos
            if update_callback: update_callback({'status': 'Aguardando 3 segundos...'})
            for _ in range(3):
                if check_pause_stop(): return
                time.sleep(1)
            
            # 6. Clicar em selecionar todos
            if check_pause_stop(): return
            if update_callback: update_callback({'status': 'Selecionando todos os itens...'})
            pyautogui.click(coords['btn_selecionar_todos'][0], coords['btn_selecionar_todos'][1])
            
            # 7. Aguardar 3 segundos
            if update_callback: update_callback({'status': 'Aguardando 3 segundos...'})
            for _ in range(3):
                if check_pause_stop(): return
                time.sleep(1)
                
            # 8. Teclar F4 aguarda 1 segundo
            if check_pause_stop(): return
            if update_callback: update_callback({'status': 'Pressionando F4...'})
            pyautogui.press('f4')
            time.sleep(1)

            # 9. Teclar Enter aguarda 1 segundo
            if check_pause_stop(): return
            if update_callback: update_callback({'status': 'Pressionando Enter...'})
            pyautogui.press('enter')
            time.sleep(1)

            # 10. Aguardar 60 segundos (1 minuto)
            if update_callback: update_callback({'status': 'Aguardando 1 minuto para processamento...'})
            for _ in range(60):
                if check_pause_stop(): return
                time.sleep(1)
                
            # 11. Teclar Enter
            if check_pause_stop(): return
            if update_callback: update_callback({'status': 'Pressionando Enter (finalização)...'})
            pyautogui.press('enter')
            
            # 12. 1 segundo depois "F10"
            time.sleep(1.0)
            if check_pause_stop(): return
            if update_callback: update_callback({'status': 'Pressionando F10...'})
            pyautogui.press('f10')

            # Finalização
            time.sleep(1)
            if update_callback:
                update_callback({'status': 'Concluído', 'finished': True, 'log': 'Macro de aprovação executada com sucesso.'})
            
        except Exception as e:
            if update_callback:
                update_callback({'error': f"Erro durante a execução: {str(e)}"})

    def calibrate(self, parent_window):
        # Janela de calibração nos mesmos moldes do ap.py
        import threading

        class CalibrationAprovacaoWindow(tk.Toplevel):
            def __init__(self, parent):
                super().__init__(parent)
                self.title("Calibração - Aprovação Automática")
                self.geometry("450x300")
                self.resizable(False, False)
                self.transient(parent)
                self.grab_set()

                self.coords = {"btn_aprovar": None, "btn_selecionar_todos": None}
                self.load_existing_coords()

                tk.Label(self, text="Assistente de Calibração", font=("Segoe UI", 12, "bold")).pack(pady=10)
                tk.Label(self, text="Siga as instruções abaixo para mapear os botões.", wraplength=400).pack(pady=5)

                self.btn_aprovar = tk.Button(self, text="1. Capturar Botão 'Aprovar' (Pós Alt+M)", command=lambda: self.start_capture("btn_aprovar"), width=40)
                self.btn_aprovar.pack(pady=10)
                self.lbl_aprovar = tk.Label(self, text="Não definido", fg="red")
                self.lbl_aprovar.pack()

                self.btn_selecionar_todos = tk.Button(self, text="2. Capturar Botão 'Selecionar Todos'", command=lambda: self.start_capture("btn_selecionar_todos"), width=40)
                self.btn_selecionar_todos.pack(pady=10)
                self.lbl_selecionar_todos = tk.Label(self, text="Não definido", fg="red")
                self.lbl_selecionar_todos.pack()

                self.btn_save = tk.Button(self, text="Salvar e Fechar", command=self.save_coords, state="disabled", bg="#4CAF50", fg="white")
                self.btn_save.pack(pady=20, fill='x', padx=20)

                self.update_initial_view()

            def load_existing_coords(self):
                coords_file = BaseAction.get_coords_path('coords.json')
                if os.path.exists(coords_file):
                    try:
                        with open(coords_file, 'r') as f:
                            saved = json.load(f)
                            if "btn_aprovar" in saved:
                                self.coords["btn_aprovar"] = saved["btn_aprovar"]
                            if "btn_selecionar_todos" in saved:
                                self.coords["btn_selecionar_todos"] = saved["btn_selecionar_todos"]
                    except Exception:
                        pass

            def update_initial_view(self):
                if self.coords.get("btn_aprovar"):
                    x, y = self.coords["btn_aprovar"]
                    self.lbl_aprovar.config(text=f"Salvo: {x}, {y}", fg="green")
                if self.coords.get("btn_selecionar_todos"):
                    x, y = self.coords["btn_selecionar_todos"]
                    self.lbl_selecionar_todos.config(text=f"Salvo: {x}, {y}", fg="green")

                if all(self.coords.values()):
                    self.btn_save.config(state="normal")

            def start_capture(self, key):
                btn = self.btn_aprovar if key == "btn_aprovar" else self.btn_selecionar_todos
                orig_text = btn.cget("text")
                btn.config(text="Aponte o mouse e dê um CLIQUE...", state="disabled")
                threading.Thread(target=self.capture_thread, args=(key, btn, orig_text), daemon=True).start()

            def capture_thread(self, key, btn, orig_text):
                from pynput import mouse
                click_x, click_y = 0, 0
                
                def on_click(x, y, button, pressed):
                    nonlocal click_x, click_y
                    if pressed and button == mouse.Button.left:
                        click_x, click_y = int(x), int(y)
                        return False # Stop listener
                        
                with mouse.Listener(on_click=on_click) as listener:
                    listener.join()

                self.coords[key] = [click_x, click_y]
                self.after(0, lambda: self.update_ui_after_capture(key, click_x, click_y, btn, orig_text))

            def update_ui_after_capture(self, key, x, y, btn, orig_text):
                btn.config(text=orig_text, state="normal")
                lbl = self.lbl_aprovar if key == "btn_aprovar" else self.lbl_selecionar_todos
                lbl.config(text=f"Capturado: {x}, {y}", fg="green")

                if all(self.coords.values()):
                    self.btn_save.config(state="normal")

            def save_coords(self):
                all_coords = {}
                coords_file = BaseAction.get_coords_path('coords.json')
                if os.path.exists(coords_file):
                    try:
                        with open(coords_file, 'r') as f:
                            all_coords = json.load(f)
                    except:
                        pass
                
                all_coords.update(self.coords)
                with open(coords_file, 'w') as f:
                    json.dump(all_coords, f)
                    
                messagebox.showinfo("Sucesso", "Coordenadas capturadas e salvas com sucesso!", parent=self)
                self.destroy()

        CalibrationAprovacaoWindow(parent_window)

def get_action():
    return AcaoAprovarPedido()
