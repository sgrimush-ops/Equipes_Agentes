import tkinter as tk
from tkinter import messagebox, ttk
import threading
import json
import os
import sys
from pynput import mouse

def _get_coords_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'coords', 'coords.json')

class MargemObjetivaCalibrationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calibração - Ajuste de Margem Objetiva")
        self.geometry("450x350")
        
        self.coords = {}
        self.load_existing_coords()
        
        self.expected_keys = [
            "campo_familia_margem",
            "aba_divisao_margem",
            "linha_divisao_margem",
            "campo_preenchimento_margem"
        ]
            
        self.buttons = {}
        self.labels = {}
        
        tk.Label(self, text="Mapeamento de Botões (Margem Objetiva)", font=("Segoe UI", 12, "bold")).pack(pady=10)
        tk.Label(self, text="Mapeie os 4 locais exatos onde o robô deve clicar.", wraplength=400).pack(pady=5)
        
        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.create_calibration_row(container, "1. Campo Código Família", "campo_familia_margem")
        self.create_calibration_row(container, "2. Aba Divisão Mapeada", "aba_divisao_margem")
        self.create_calibration_row(container, "3. Linha Mapeada (Duplo Clique)", "linha_divisao_margem")
        self.create_calibration_row(container, "4. Área Preenchimento Margem", "campo_preenchimento_margem")

        self.btn_save = tk.Button(self, text="Salvar Calibração e Fechar", command=self.save_coords, bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"))
        self.btn_save.pack(fill="x", padx=20, pady=15)

    def create_calibration_row(self, container, display_text, key):
        row = tk.Frame(container)
        row.pack(fill="x", pady=5)
        
        btn = tk.Button(row, text=display_text, width=35, command=lambda k=key: self.start_capture(k))
        btn.pack(side="left", padx=5)
        
        lbl = tk.Label(row, text="Não definido", fg="red", width=20, anchor="w")
        lbl.pack(side="left", padx=5)
        
        self.buttons[key] = btn
        self.labels[key] = lbl
        
        if key in self.coords and self.coords[key]:
            x, y = self.coords[key]
            lbl.config(text=f"Salvo: {x}, {y}", fg="green")

    def load_existing_coords(self):
        coords_path = _get_coords_path()
        if os.path.exists(coords_path):
            try:
                with open(coords_path, 'r') as f:
                    self.coords = json.load(f)
            except Exception:
                pass

    def start_capture(self, key):
        btn = self.buttons[key]
        orig_text = btn.cget("text")
        btn.config(text="Aponte e dê um CLIQUE", state="disabled", bg="yellow")
        
        threading.Thread(target=self.capture_thread, args=(key, btn, orig_text), daemon=True).start()

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
        btn.config(text=orig_text, state="normal", bg="SystemButtonFace")
        self.labels[key].config(text=f"Capturado: {x}, {y}", fg="green")

    def save_coords(self):
        current_data = {}
        coords_path = _get_coords_path()
        
        if os.path.exists(coords_path):
            try:
                with open(coords_path, 'r') as f:
                    current_data = json.load(f)
            except Exception:
                pass
                
        for k in self.expected_keys:
            if k in self.coords:
                current_data[k] = self.coords[k]
                
        os.makedirs(os.path.dirname(coords_path), exist_ok=True)
                
        with open(coords_path, 'w') as f:
            json.dump(current_data, f)
            
        messagebox.showinfo("Sucesso", "Coordenadas salvas com sucesso!")
        self.destroy()
