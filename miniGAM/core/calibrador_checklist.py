import os
import sys
import json
import threading
import tkinter as tk
from tkinter import messagebox
from pynput import mouse
from typing import Dict, Any, List, Optional

def get_coords_filepath() -> str:
    """Retorna o caminho do coords_minigam.json ao lado do executável (compatível com pendrive)."""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "coords_minigam.json")


class CalibradorChecklist(tk.Toplevel):
    """
    Interface visual de calibração para o Mini-GAM.
    Mapeia:
    - X e Y da Linha 1 na coluna Título
    - X da coluna Valor em Aberto
    - X da coluna do Checkbox (Qui)
    - Y da Linha 12 (última linha visível no grid)
    A partir disso, calcula automaticamente as 12 coordenadas equidistantes das linhas visíveis.
    """
    def __init__(self, parent: tk.Tk, on_save_callback=None):
        super().__init__(parent)
        self.title("Mapear Checklist - Calibração de Coordenadas")
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(bg="#f8f9fa")
        self.attributes("-topmost", True)

        self.on_save_callback = on_save_callback
        self.coords: Dict[str, Any] = {
            "x_titulo": None,
            "x_valor": None,
            "x_checkbox": None,
            "y_linha_1": None,
            "y_linha_12": None,
            "linhas_y": []
        }
        self.load_coords()

        self.create_widgets()
        self.update_ui_state()

    def load_coords(self):
        path = get_coords_filepath()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.coords.update(data)
            except Exception as e:
                print(f"[Calibrador] Erro ao carregar coordenadas: {e}")

    def save_coords_to_file(self):
        # Calcula as 12 linhas equidistantes de Y antes de salvar
        if self.coords["y_linha_1"] is not None and self.coords["y_linha_12"] is not None:
            y1 = float(self.coords["y_linha_1"])
            y12 = float(self.coords["y_linha_12"])
            
            if abs(y12 - y1) < 80:
                msg = f"A distância entre a Linha 1 (Y={int(y1)}) e a Linha 12 (Y={int(y12)}) é de apenas {int(abs(y12-y1))} pixels!\n\nEm uma tela real com 12 linhas, a distância costuma ser maior que 180 pixels.\n\nVocê tem certeza de que clicou no topo da tabela para a Linha 1 e no fundo da parte visível da tabela para a Linha 12?"
                if not messagebox.askyesno("Atenção: Distância Muito Curta", msg):
                    return

            linhas = []
            for i in range(12):
                # Interpolação linear exata das 12 linhas (índices 0 a 11)
                y_i = int(round(y1 + i * (y12 - y1) / 11.0))
                linhas.append(y_i)
            self.coords["linhas_y"] = linhas

        path = get_coords_filepath()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.coords, f, indent=4)
            messagebox.showinfo("Calibração Concluída", f"Coordenadas salvas com sucesso em:\n{os.path.basename(path)}")
            if self.on_save_callback:
                self.on_save_callback(self.coords)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo json: {e}")

    def create_widgets(self):
        header = tk.Frame(self, bg="#2c3e50", pady=12)
        header.pack(fill="x")
        tk.Label(
            header, text="⚙️ Mapeamento do Grid Consinco",
            font=("Segoe UI", 13, "bold"), fg="white", bg="#2c3e50"
        ).pack()

        body = tk.Frame(self, bg="#f8f9fa", padx=20, pady=15)
        body.pack(fill="both", expand=True)

        tk.Label(
            body, text="⚠️ IMPORTANTE: Clique sempre nos REGISTROS DE DADOS da tabela (ex: linha '9-700/1' e valor '37,44'). NUNCA clique na barra cinza de cabeçalho ('Título'/'Valor em Aberto')!",
            font=("Segoe UI", 9, "bold"), bg="#fff3cd", fg="#856404", wraplength=440, justify="left", padx=8, pady=6, bd=1, relief="solid"
        ).pack(pady=(0, 15), fill="x")

        # Botão 1: Coluna Título na Linha 1 de dados
        self.btn_titulo = tk.Button(
            body, text="1. Capturar Título (1ª Linha DADOS - 2 CLIQUES: Esq e Dir)",
            font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#2b2d42", relief="groove",
            command=lambda: self.start_capture("titulo_l1", self.btn_titulo, self.lbl_titulo)
        )
        self.btn_titulo.pack(fill="x", pady=4)
        self.lbl_titulo = tk.Label(body, text="Não definido", font=("Consolas", 9), bg="#f8f9fa", fg="#d90429")
        self.lbl_titulo.pack(anchor="w", padx=5)

        # Botão 2: Coluna Valor em Aberto na Linha 1 de dados
        self.btn_valor = tk.Button(
            body, text="2. Capturar Valor em Aberto (1ª Linha DADOS - 2 CLIQUES: Esq e Dir)",
            font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#2b2d42", relief="groove",
            command=lambda: self.start_capture("valor_l1", self.btn_valor, self.lbl_valor)
        )
        self.btn_valor.pack(fill="x", pady=4)
        self.lbl_valor = tk.Label(body, text="Não definido", font=("Consolas", 9), bg="#f8f9fa", fg="#d90429")
        self.lbl_valor.pack(anchor="w", padx=5)

        # Botão 3: Coluna Checkbox (Qui) na Linha 1 de dados
        self.btn_check_l1 = tk.Button(
            body, text="3. Capturar Checkbox Qui (1ª Linha DADOS - 1 CLIQUE central)",
            font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#2b2d42", relief="groove",
            command=lambda: self.start_capture("checkbox_l1", self.btn_check_l1, self.lbl_check_l1)
        )
        self.btn_check_l1.pack(fill="x", pady=4)
        self.lbl_check_l1 = tk.Label(body, text="Não definido", font=("Consolas", 9), bg="#f8f9fa", fg="#d90429")
        self.lbl_check_l1.pack(anchor="w", padx=5)

        # Botão 4: Coluna Checkbox (Qui) na Linha 12 de dados
        self.btn_l12 = tk.Button(
            body, text="4. Capturar Checkbox Qui (12ª Linha DADOS - 1 CLIQUE central)",
            font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#2b2d42", relief="groove",
            command=lambda: self.start_capture("linha_12", self.btn_l12, self.lbl_l12)
        )
        self.btn_l12.pack(fill="x", pady=4)
        self.lbl_l12 = tk.Label(body, text="Não definido", font=("Consolas", 9), bg="#f8f9fa", fg="#d90429")
        self.lbl_l12.pack(anchor="w", padx=5)

        footer = tk.Frame(self, bg="#f8f9fa", pady=10)
        footer.pack(fill="x", padx=20)

        self.btn_save = tk.Button(
            footer, text="✅ Salvar Coordenadas e Fechar",
            font=("Segoe UI", 11, "bold"), bg="#2a9d8f", fg="white", state="disabled",
            command=self.save_coords_to_file, pady=6
        )
        self.btn_save.pack(fill="x")

    def update_ui_state(self):
        if self.coords.get("x_titulo_esq") is not None and self.coords.get("x_titulo_dir") is not None:
            w = abs(self.coords["x_titulo_dir"] - self.coords["x_titulo_esq"])
            self.lbl_titulo.config(text=f"Salvo: Esq={self.coords['x_titulo_esq']}, Dir={self.coords['x_titulo_dir']} (Largura: {w}px) | Y={self.coords['y_linha_1']}", fg="#2a9d8f")
        elif self.coords["x_titulo"] and self.coords["y_linha_1"]:
            self.lbl_titulo.config(text=f"Salvo: X={self.coords['x_titulo']}, Y={self.coords['y_linha_1']}", fg="#2a9d8f")

        if self.coords.get("x_valor_esq") is not None and self.coords.get("x_valor_dir") is not None:
            w = abs(self.coords["x_valor_dir"] - self.coords["x_valor_esq"])
            self.lbl_valor.config(text=f"Salvo: Esq={self.coords['x_valor_esq']}, Dir={self.coords['x_valor_dir']} (Largura: {w}px)", fg="#2a9d8f")
        elif self.coords["x_valor"]:
            self.lbl_valor.config(text=f"Salvo: X={self.coords['x_valor']}", fg="#2a9d8f")

        if self.coords["x_checkbox"] and self.coords["y_linha_1"]:
            self.lbl_check_l1.config(text=f"Salvo: X={self.coords['x_checkbox']}, Y={self.coords['y_linha_1']}", fg="#2a9d8f")
        if self.coords["y_linha_12"]:
            self.lbl_l12.config(text=f"Salvo: Y={self.coords['y_linha_12']}", fg="#2a9d8f")

        if all([self.coords["x_titulo"], self.coords["x_valor"], self.coords["x_checkbox"], self.coords["y_linha_1"], self.coords["y_linha_12"]]):
            self.btn_save.config(state="normal")

    def start_capture(self, mode_key: str, btn: tk.Button, lbl: tk.Label):
        orig_text = btn.cget("text")
        if mode_key in ["titulo_l1", "valor_l1"]:
            btn.config(text="👉 1º CLIQUE: Aponte no canto ESQUERDO e clique...", bg="#ffb703", fg="#000000", state="disabled")
            lbl.config(text="Aguardando 1º clique (Canto Esquerdo)...", fg="#e76f51")
        else:
            btn.config(text="👉 Aponte na tela e CLIQUE AGORA...", bg="#ffb703", fg="#000000", state="disabled")
            lbl.config(text="Aguardando clique na tela...", fg="#e76f51")

        threading.Thread(target=self._capture_thread, args=(mode_key, btn, lbl, orig_text), daemon=True).start()

    def _capture_thread(self, mode_key: str, btn: tk.Button, lbl: tk.Label, orig_text: str):
        if mode_key in ["titulo_l1", "valor_l1"]:
            x_clicks = []
            y_clicks = []

            def on_click_two(x, y, button, pressed):
                if pressed and button == mouse.Button.left:
                    x_clicks.append(int(x))
                    y_clicks.append(int(y))
                    if len(x_clicks) == 1:
                        # Pede o 2º clique no canto direito
                        self.after(0, lambda: btn.config(text="👉 2º CLIQUE: Agora aponte no canto DIREITO e clique..."))
                        self.after(0, lambda: lbl.config(text=f"Esq: X={int(x)}. Aguardando 2º clique (Canto Direito)..."))
                    if len(x_clicks) >= 2:
                        return False

            with mouse.Listener(on_click=on_click_two) as listener:
                listener.join()

            x_esq = min(x_clicks[0], x_clicks[1])
            x_dir = max(x_clicks[0], x_clicks[1])
            x_centro = int((x_esq + x_dir) / 2)
            y_centro = int((y_clicks[0] + y_clicks[1]) / 2)

            if mode_key == "titulo_l1":
                self.coords["x_titulo_esq"] = x_esq
                self.coords["x_titulo_dir"] = x_dir
                self.coords["x_titulo"] = x_centro
                self.coords["y_linha_1"] = y_centro
            elif mode_key == "valor_l1":
                self.coords["x_valor_esq"] = x_esq
                self.coords["x_valor_dir"] = x_dir
                self.coords["x_valor"] = x_centro
                if not self.coords["y_linha_1"]:
                    self.coords["y_linha_1"] = y_centro

            self.after(0, lambda: self._after_capture_ui(btn, lbl, orig_text, x_centro, y_centro))
        else:
            click_x, click_y = 0, 0

            def on_click(x, y, button, pressed):
                nonlocal click_x, click_y
                if pressed and button == mouse.Button.left:
                    click_x, click_y = int(x), int(y)
                    return False  # Encerra o listener do mouse

            with mouse.Listener(on_click=on_click) as listener:
                listener.join()

            if mode_key == "checkbox_l1":
                self.coords["x_checkbox"] = click_x
                if not self.coords["y_linha_1"]:
                    self.coords["y_linha_1"] = click_y
            elif mode_key == "linha_12":
                self.coords["y_linha_12"] = click_y
                if not self.coords["x_checkbox"]:
                    self.coords["x_checkbox"] = click_x

            self.after(0, lambda: self._after_capture_ui(btn, lbl, orig_text, click_x, click_y))

    def _after_capture_ui(self, btn: tk.Button, lbl: tk.Label, orig_text: str, x: int, y: int):
        btn.config(text=orig_text, bg="#ffffff", fg="#2b2d42", state="normal")
        self.update_ui_state()
