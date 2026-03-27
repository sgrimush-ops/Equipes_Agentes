import os
import time
import json
import threading
import tkinter as tk
from tkinter import messagebox
from pynput import mouse
import pyautogui
from actions.base_action import BaseAction

class BloqueioCalibrationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calibração - Bloquear Tela")
        self.geometry("400x350")
        self.resizable(False, False)
        
        self.coords_file = 'coords/coords_bloqueio.json'
        self.coords = {"btn_iniciar": None, "btn_power": None, "btn_bloquear": None}
        self.load_existing_coords()
        
        tk.Label(self, text="Calibração do Bloqueio de Tela", font=("Segoe UI", 12, "bold")).pack(pady=10)
        tk.Label(self, text="Siga os botões na ordem.", wraplength=380).pack(pady=5)
        
        # Iniciar
        self.btn_iniciar = tk.Button(self, text="1. Botão Iniciar", command=lambda: self.start_capture("btn_iniciar"), width=30)
        self.btn_iniciar.pack(pady=5)
        self.lbl_iniciar = tk.Label(self, text="Não definido", fg="red")
        self.lbl_iniciar.pack()
        
        # Power / Perfil
        self.btn_power = tk.Button(self, text="2. Botão Power/Perfil", command=lambda: self.start_capture("btn_power"), width=30)
        self.btn_power.pack(pady=5)
        self.lbl_power = tk.Label(self, text="Não definido", fg="red")
        self.lbl_power.pack()
        
        # Bloquear
        self.btn_bloquear = tk.Button(self, text="3. Botão Bloquear", command=lambda: self.start_capture("btn_bloquear"), width=30)
        self.btn_bloquear.pack(pady=5)
        self.lbl_bloquear = tk.Label(self, text="Não definido", fg="red")
        self.lbl_bloquear.pack()
        
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
        for key, lbl in [("btn_iniciar", self.lbl_iniciar), ("btn_power", self.lbl_power), ("btn_bloquear", self.lbl_bloquear)]:
            if self.coords.get(key):
                x, y = self.coords[key]
                lbl.config(text=f"Salvo: {x}, {y}", fg="green")
        if all(self.coords.values()):
            self.btn_save.config(state="normal")

    def start_capture(self, key):
        btns = {"btn_iniciar": self.btn_iniciar, "btn_power": self.btn_power, "btn_bloquear": self.btn_bloquear}
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
        labels = {"btn_iniciar": ("1. Botão Iniciar", self.lbl_iniciar), 
                  "btn_power": ("2. Botão Power/Perfil", self.lbl_power),
                  "btn_bloquear": ("3. Botão Bloquear", self.lbl_bloquear)}
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


class AcaoBloquearTela(BaseAction):
    @property
    def name(self) -> str:
        return "Bloquear Tela"
        
    @property
    def description(self) -> str:
        return "Bloqueia a tela do Windows instantaneamente (usando comando nativo)."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if update_callback:
            update_callback({'status': 'Bloqueando tela...', 'log': 'Bloqueando o Windows em 3s...'})
        
        time.sleep(3)
        if stop_event and stop_event.is_set(): return
        
        # Bloqueio de tela nativo do Windows (muito mais confiável que cliques do mouse)
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        
        if update_callback:
            update_callback({'status': 'Concluído', 'finished': True, 'log': 'Tela Bloqueada.'})

    def has_calibration(self) -> bool:
        return False
        
    def calibrate(self, parent_window):
        pass

def get_action():
    return AcaoBloquearTela()
