import os
import time
import json
import threading
import tkinter as tk
from tkinter import messagebox
from pynput import mouse
import pyautogui
import webbrowser
from actions.base_action import BaseAction

class WhatsappCalibrationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calibração - WhatsApp")
        self.geometry("450x450")
        self.resizable(False, False)
        
        self.coords_file = 'coords/coords_whatsapp.json'
        self.coords = {
            "pos_busca": None, 
            "pos_grupo": None, 
            "pos_texto": None, 
            "pos_enviar": None
        }
        self.load_existing_coords()
        
        tk.Label(self, text="Calibração do WhatsApp Web", font=("Segoe UI", 12, "bold")).pack(pady=10)
        tk.Label(self, text="Abra o WhatsApp Web e mapeie os 4 pontos abaixo.", wraplength=400).pack(pady=5)
        
        # 1. Busca
        self.btn_busca = tk.Button(self, text="1. Campo 'Pesquisar Contato'", command=lambda: self.start_capture("pos_busca"), width=35)
        self.btn_busca.pack(pady=5)
        self.lbl_busca = tk.Label(self, text="Não definido", fg="red")
        self.lbl_busca.pack()
        
        # 2. Grupo
        self.btn_grupo = tk.Button(self, text="2. Clicar no Grupo Encontrado", command=lambda: self.start_capture("pos_grupo"), width=35)
        self.btn_grupo.pack(pady=5)
        self.lbl_grupo = tk.Label(self, text="Não definido", fg="red")
        self.lbl_grupo.pack()
        
        # 3. Texto
        self.btn_texto = tk.Button(self, text="3. Campo de Digitar Mensagem", command=lambda: self.start_capture("pos_texto"), width=35)
        self.btn_texto.pack(pady=5)
        self.lbl_texto = tk.Label(self, text="Não definido", fg="red")
        self.lbl_texto.pack()

        # 4. Enviar
        self.btn_enviar = tk.Button(self, text="4. Botão de Enviar (Setinha)", command=lambda: self.start_capture("pos_enviar"), width=35)
        self.btn_enviar.pack(pady=5)
        self.lbl_enviar = tk.Label(self, text="Não definido", fg="red")
        self.lbl_enviar.pack()
        
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
        labels_map = {
            "pos_busca": self.lbl_busca,
            "pos_grupo": self.lbl_grupo,
            "pos_texto": self.lbl_texto,
            "pos_enviar": self.lbl_enviar
        }
        for key, lbl in labels_map.items():
            if self.coords.get(key):
                x, y = self.coords[key]
                lbl.config(text=f"Salvo: {x}, {y}", fg="green")
        if all(self.coords.values()):
            self.btn_save.config(state="normal")

    def start_capture(self, key):
        btns_map = {
            "pos_busca": self.btn_busca,
            "pos_grupo": self.btn_grupo,
            "pos_texto": self.btn_texto,
            "pos_enviar": self.btn_enviar
        }
        btn = btns_map[key]
        btn.config(text="Aponte e CLIQUE com botão Esquerdo", state="disabled")
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
        labels_map = {
            "pos_busca": ("1. Campo 'Pesquisar Contato'", self.lbl_busca), 
            "pos_grupo": ("2. Clicar no Grupo Encontrado", self.lbl_grupo),
            "pos_texto": ("3. Campo de Digitar Mensagem", self.lbl_texto),
            "pos_enviar": ("4. Botão de Enviar (Setinha)", self.lbl_enviar)
        }
        original_title, lbl = labels_map[key]
        
        btn.config(text=original_title, state="normal")
        lbl.config(text=f"Capturado: {x}, {y}", fg="green")
        
        if all(self.coords.values()):
            self.btn_save.config(state="normal")

    def save_coords(self):
        with open(self.coords_file, 'w') as f:
            json.dump(self.coords, f)
        messagebox.showinfo("Sucesso", "Coordenadas salvas com sucesso!")
        self.destroy()


class AcaoWhatsapp(BaseAction):
    @property
    def name(self) -> str:
        return "Enviar Msg WhatsApp"
        
    @property
    def description(self) -> str:
        return "Abre o WhatsApp Web e notifica o grupo Robo."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if not os.path.exists('coords/coords_whatsapp.json'):
            if update_callback:
                update_callback({'error': "Coordenadas não calibradas para WhatsApp. Clique em Calibrar na ação."})
            return
            
        try:
            with open('coords/coords_whatsapp.json', 'r') as f:
                coords = json.load(f)
        except Exception as e:
            if update_callback: update_callback({'error': f"Erro ao ler coordenadas: {e}"})
            return
            
        pos_busca = coords.get("pos_busca")
        pos_grupo = coords.get("pos_grupo")
        pos_texto = coords.get("pos_texto")
        pos_enviar = coords.get("pos_enviar")
        
        if not all([pos_busca, pos_grupo, pos_texto, pos_enviar]):
            if update_callback:
                update_callback({'error': "Calibração do WhatsApp incompleta. Calibre novamente."})
            return

        if update_callback:
            update_callback({'status': 'Abrindo WhatsApp...', 'log': 'Iniciando navegador e abrindo WhatsApp Web...'})
        
        # 1 e 2. Abrir Navegador e WhatsApp
        webbrowser.open('https://web.whatsapp.com/')
        
        # 4. Aguardar 30 segundos para carregar o site completamente (com possibilidade de interrupção)
        for _ in range(300):
            if stop_event and stop_event.is_set(): return
            time.sleep(0.1)
            
        if update_callback: update_callback({'log': 'Procurando contato...'})
            
        # 5. Clicar no campo de pesquisar
        pyautogui.moveTo(pos_busca[0], pos_busca[1], duration=0.2)
        time.sleep(0.5)
        pyautogui.click()
        time.sleep(0.5)
        if stop_event and stop_event.is_set(): return
        
        # 6. Digitar "GAM"
        pyautogui.write("GAM", interval=0.1)
        time.sleep(1.5) # Aguarda a busca mostrar resultados
        if stop_event and stop_event.is_set(): return
        
        # 7. Clicar no grupo encontrado
        if update_callback: update_callback({'log': 'Abrindo grupo...'})
        pyautogui.moveTo(pos_grupo[0], pos_grupo[1], duration=0.2)
        time.sleep(0.5)
        pyautogui.click()
        time.sleep(1.5) # Aguarda abrir o chat
        if stop_event and stop_event.is_set(): return
        
        # 8. Clicar no campo de texto
        if update_callback: update_callback({'log': 'Escrevendo mensagem...'})
        pyautogui.moveTo(pos_texto[0], pos_texto[1], duration=0.2)
        time.sleep(0.5)
        pyautogui.click()
        time.sleep(0.5)
        if stop_event and stop_event.is_set(): return
        
        # 9. Digitar a mensagem
        pyautogui.write("Gam, terminou de digitar a tarefa", interval=0.05)
        time.sleep(1)
        if stop_event and stop_event.is_set(): return
        
        # 10. Clicar em Enviar
        if update_callback: update_callback({'log': 'Enviando...'})
        pyautogui.moveTo(pos_enviar[0], pos_enviar[1], duration=0.2)
        time.sleep(0.5)
        pyautogui.click()
        time.sleep(1)
        
        if update_callback:
            update_callback({'status': 'Concluído', 'finished': True, 'log': 'Mensagem de WhatsApp enviada.'})

    def has_calibration(self) -> bool:
        return True
        
    def calibrate(self, parent_window):
        WhatsappCalibrationWindow(parent_window)

def get_action():
    return AcaoWhatsapp()
