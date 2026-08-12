import tkinter as tk
from tkinter import messagebox
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

class AbastecimentoCalibrationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calibração - Forma de Abastecimento")
        self.geometry("500x650")
        
        self.coords = {}
        self.load_existing_coords()
        
        self.expected_keys = [
            "campo_codigo_abastecimento",
            "botao_familia_abastecimento",
            "aba_divisao_abastecimento",
            "linha_categoria_abastecimento",
            "campo_forma_abastecimento",
            "posicao_M_abastecimento",
            "posicao_C_abastecimento",
            "posicao_L_abastecimento",
            "posicao_I_abastecimento",
            "aba_logis_abast_abastecimento",
            "aba_geral_abastecimento",
            "linha_cd15_abastecimento",
            "linha_cd16_abastecimento"
        ]
            
        self.buttons = {}
        self.labels = {}
        
        tk.Label(self, text="Mapeamento de Botões (Forma de Abastecimento)", font=("Segoe UI", 12, "bold")).pack(pady=10)
        tk.Label(self, text="Mapeie os 8 locais exatos onde o robô deve clicar.", wraplength=450).pack(pady=5)
        
        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.create_calibration_row(container, "1. Campo Código Produto", "campo_codigo_abastecimento")
        self.create_calibration_row(container, "2. Botão Família", "botao_familia_abastecimento")
        self.create_calibration_row(container, "3. Aba Divisão", "aba_divisao_abastecimento")
        self.create_calibration_row(container, "4. Categoria (Duplo Clique)", "linha_categoria_abastecimento")
        self.create_calibration_row(container, "5. Dropdown Abastecimento", "campo_forma_abastecimento")
        self.create_calibration_row(container, "6. Posição M", "posicao_M_abastecimento")
        self.create_calibration_row(container, "7. Posição C", "posicao_C_abastecimento")
        self.create_calibration_row(container, "8. Posição L", "posicao_L_abastecimento")
        self.create_calibration_row(container, "9. Posição I (Inversa)", "posicao_I_abastecimento")
        self.create_calibration_row(container, "10. Aba Empresa/Segmento", "aba_logis_abast_abastecimento")
        self.create_calibration_row(container, "11. Aba Geral", "aba_geral_abastecimento")
        self.create_calibration_row(container, "12. Linha CD15 (Emp/Segm)", "linha_cd15_abastecimento")
        self.create_calibration_row(container, "13. Linha CD16 (Emp/Segm)", "linha_cd16_abastecimento")

        self.btn_save = tk.Button(self, text="Salvar Calibração e Fechar", command=self.save_coords, bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"))
        self.btn_save.pack(fill="x", padx=20, pady=15)

    def create_calibration_row(self, container, display_text, key):
        row = tk.Frame(container)
        row.pack(fill="x", pady=2)
        
        btn = tk.Button(row, text=display_text, width=30, command=lambda k=key: self.start_capture(k))
        btn.pack(side="left", padx=5)
        
        lbl = tk.Label(row, text="Não definido", fg="red", width=25, anchor="w")
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
