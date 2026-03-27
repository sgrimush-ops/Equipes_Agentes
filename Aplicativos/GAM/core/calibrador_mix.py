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
        # Pega a raiz do projeto já que este arquivo está em core/
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'coords', 'coords.json')

class MixCalibrationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calibração - Mix Ativo")
        self.geometry("450x600")
        
        self.coords = {}
        self.load_existing_coords()
        
        # Configurar as chaves esperadas
        self.expected_keys = ["empresa_mix"]
        self.store_list = [
            "001", "002", "003", "004", "005", "006", "007", "008", 
            "009", "010", "011", "012", "013", "014", "015", "016", 
            "017", "018", "020", "021", "022", "023", "050", "900", 
            "901", "902"
        ]
        for s in self.store_list:
            self.expected_keys.append(f"loja_{s}")
            
        self.buttons = {}
        self.labels = {}
        
        tk.Label(self, text="Mapeamento de Botões (Mix Ativo)", font=("Segoe UI", 12, "bold")).pack(pady=10)
        tk.Label(self, text="1. Botão 'Empresa'\n2. Mapeamento das 26 Lojas visíveis.", wraplength=400).pack(pady=5)
        
        # Frame rolável para caber os 27 botões
        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Criar as linhas (Botão + Label) para cada chave
        self.create_calibration_row("Coordenada: Botão 'Empresa'", "empresa_mix")
        tk.Frame(self.scrollable_frame, height=2, bg="gray").pack(fill="x", pady=10) # Separador
        
        for st in self.store_list:
            display_name = f"Coordenada: Loja {st}"
            if st == "015": display_name = "Coordenada: CD 15"
            elif st == "016": display_name = "Coordenada: CD 16"
            elif st == "050": display_name = "Coordenada: CD 50"
            elif st == "021": display_name = "Coordenada: Atacado 21"
            elif st in ["022", "023"]: display_name = f"Coordenada: Usina {st}"
            elif st == "900": display_name = "Coordenada: ADM (900)"
            elif st == "901": display_name = "Coordenada: AloServ (901)"
            elif st == "902": display_name = "Coordenada: Remopar (902)"
            
            self.create_calibration_row(display_name, f"loja_{st}")

        # Botão de Salvar Global
        self.btn_save = tk.Button(self, text="Salvar Calibração e Fechar", command=self.save_coords, bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"))
        self.btn_save.pack(fill="x", padx=20, pady=10)
        self.check_if_can_save()

    def create_calibration_row(self, display_text, key):
        row = tk.Frame(self.scrollable_frame)
        row.pack(fill="x", pady=2)
        
        btn = tk.Button(row, text=display_text, width=30, command=lambda k=key: self.start_capture(k))
        btn.pack(side="left", padx=5)
        
        lbl = tk.Label(row, text="Não definido", fg="red", width=20, anchor="w")
        lbl.pack(side="left", padx=5)
        
        self.buttons[key] = btn
        self.labels[key] = lbl
        
        # Update view if already exists
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

    def check_if_can_save(self):
        # Permitimos salvar mesmo sem mapear todas (pode não querer ativar tudo do zero)
        # O robô avisa se faltar no run()
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
        self.check_if_can_save()

    def save_coords(self):
        # Carrega o JSON atual para não apagar chaves do CD (ex: cd_abastecedor)
        current_data = {}
        coords_path = _get_coords_path()
        
        if os.path.exists(coords_path):
            try:
                with open(coords_path, 'r') as f:
                    current_data = json.load(f)
            except Exception:
                pass
                
        # Atualiza apenas as que mexemos na tela de mix
        for k in self.expected_keys:
            if k in self.coords:
                current_data[k] = self.coords[k]
                
        # Certifica-se de que a pasta existe
        os.makedirs(os.path.dirname(coords_path), exist_ok=True)
                
        with open(coords_path, 'w') as f:
            json.dump(current_data, f)
            
        messagebox.showinfo("Sucesso", "Coordenadas do Mix salvas com sucesso!")
        self.destroy()
