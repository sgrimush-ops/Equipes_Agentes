import os
import time
import json
import threading
import tkinter as tk
from tkinter import messagebox
from pynput import mouse
import pyautogui
from actions.base_action import BaseAction

class FecharTelaCalibrationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calibração - Fechar Tela Ativa")
        self.geometry("400x250")
        self.resizable(False, False)
        
        self.coords_file = 'coords/coords_fechar_tela.json'
        self.coords = {"pos_fechar": None}
        self.load_existing_coords()
        
        tk.Label(self, text="Calibração de Fechamento", font=("Segoe UI", 12, "bold")).pack(pady=10)
        tk.Label(self, text="Mapeie o botão 'X' (Fechar) da tela que você deseja que o robô encerre.", wraplength=380).pack(pady=5)
        
        # Botão Fechar
        self.btn_fechar = tk.Button(self, text="1. Capturar o Botão Fechar (X)", command=lambda: self.start_capture("pos_fechar"), width=35)
        self.btn_fechar.pack(pady=10)
        self.lbl_fechar = tk.Label(self, text="Não definido", fg="red")
        self.lbl_fechar.pack()
        
        self.btn_save = tk.Button(self, text="Salvar e Fechar", command=self.save_coords, state="disabled", bg="#4CAF50", fg="white")
        self.btn_save.pack(pady=15, fill='x', padx=20)
        
        self.update_initial_view()

    def load_existing_coords(self):
        if os.path.exists(self.coords_file):
            try:
                with open(self.coords_file, 'r') as f:
                    saved = json.load(f)
                    if "pos_fechar" in saved:
                        self.coords["pos_fechar"] = saved["pos_fechar"]
            except Exception:
                pass

    def update_initial_view(self):
        if self.coords.get("pos_fechar"):
            x, y = self.coords["pos_fechar"]
            self.lbl_fechar.config(text=f"Salvo: {x}, {y}", fg="green")
            self.btn_save.config(state="normal")

    def start_capture(self, key):
        self.btn_fechar.config(text="Aponte e CLIQUE", state="disabled")
        threading.Thread(target=self.capture_thread, args=(key, self.btn_fechar, self.btn_fechar.cget("text")), daemon=True).start()

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
        btn.config(text="1. Capturar o Botão Fechar (X)", state="normal")
        self.lbl_fechar.config(text=f"Capturado: {x}, {y}", fg="green")
        if all(self.coords.values()):
            self.btn_save.config(state="normal")

    def save_coords(self):
        with open(self.coords_file, 'w') as f:
            json.dump(self.coords, f)
        messagebox.showinfo("Sucesso", "Coordenadas salvas com sucesso!")
        self.destroy()


class AcaoFecharTelaAtiva(BaseAction):
    @property
    def name(self) -> str:
        return "Fechar Tela Ativa"
        
    @property
    def description(self) -> str:
        return "Clica na coordenada especificada (ex: botão X) para fechar uma janela."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if not os.path.exists('coords/coords_fechar_tela.json'):
            if update_callback:
                update_callback({'error': "Coordenadas não calibradas para Fechar Tela. Clique em Calibrar na ação."})
            return
            
        try:
            with open('coords/coords_fechar_tela.json', 'r') as f:
                coords = json.load(f)
        except Exception as e:
            if update_callback: update_callback({'error': f"Erro ao ler coordenadas: {e}"})
            return
            
        pos_fechar = coords.get("pos_fechar")
        
        if not pos_fechar:
            if update_callback:
                update_callback({'error': "Calibração incompleta. Calibre novamente."})
            return

        if update_callback:
            update_callback({'status': 'Fechando janela...', 'log': 'Movendo o mouse para fechar a tela...'})
        
        time.sleep(1)
        if stop_event and stop_event.is_set(): return
        
        # Mover o mouse e clicar
        pyautogui.moveTo(pos_fechar[0], pos_fechar[1], duration=0.2)
        time.sleep(0.5) # Aguardar hover nativo do Windows antes do clique
        pyautogui.click()
        
        time.sleep(1) # Esperar a janela fechar visualmente
        
        if update_callback:
            update_callback({'status': 'Concluído', 'finished': True, 'log': 'Clique de fechamento executado.'})

    def has_calibration(self) -> bool:
        return True
        
    def calibrate(self, parent_window):
        FecharTelaCalibrationWindow(parent_window)

def get_action():
    return AcaoFecharTelaAtiva()
