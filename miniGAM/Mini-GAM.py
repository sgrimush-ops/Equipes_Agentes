import os
import sys
import time
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from typing import Optional

# Adiciona o diretório atual ao sys.path para garantir imports corretos inclusive após PyInstaller
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from core.excel_manager import ExcelManager
from core.screen_reader import ScreenReader
from core.calibrador_checklist import CalibradorChecklist, get_coords_filepath
from core.runner import MiniGamRunner


class MiniGamApp:
    """
    Interface Gráfica Principal do Mini-GAM.
    Fica sobreposta acima das outras janelas (-topmost) para controle rápido
    durante a operação do Consinco.
    """
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Mini-GAM | Automação Consinco - Quitação de Título")
        self.root.geometry("640x660")
        self.root.minsize(520, 580)
        self.root.configure(bg="#212529")
        self.root.attributes("-topmost", True)

        # Instâncias do núcleo
        self.excel_manager = ExcelManager(os.path.join(base_dir, "Dados", "conferencia.xlsx"))
        self.screen_reader = ScreenReader(mode="ocr")
        self.runner = MiniGamRunner(self.excel_manager, self.screen_reader)

        self.create_widgets()
        self.check_initial_excel()
        self.update_calibration_status()

    def create_widgets(self):
        # Header Banner
        header = tk.Frame(self.root, bg="#1a1d20", pady=14)
        header.pack(fill="x")
        tk.Label(
            header, text="⚡ MINI-GAM PROTÓTIPO",
            font=("Segoe UI", 15, "bold"), fg="#f8f9fa", bg="#1a1d20"
        ).pack()
        tk.Label(
            header, text="Automação e Validação Automática de Checklists (Consinco)",
            font=("Segoe UI", 9, "italic"), fg="#adb5bd", bg="#1a1d20"
        ).pack(pady=(2, 0))

        # Main Content Frame
        main_frame = tk.Frame(self.root, bg="#212529", padx=18, pady=12)
        main_frame.pack(fill="both", expand=True)

        # --- SEÇÃO 1: BOTÕES DE AÇÃO PRINCIPAIS ---
        ctrl_frame = tk.Frame(main_frame, bg="#212529")
        ctrl_frame.pack(fill="x", pady=(0, 15))

        btn_container = tk.Frame(ctrl_frame, bg="#212529")
        btn_container.pack(expand=True)

        self.btn_comecar = tk.Button(
            btn_container, text="▶ COMEÇAR",
            font=("Segoe UI", 11, "bold"), bg="#2b9348", fg="white",
            relief="raised", bd=2, width=11, pady=8,
            command=self.acao_comecar
        )
        self.btn_comecar.grid(row=0, column=0, padx=4)

        self.btn_parar = tk.Button(
            btn_container, text="⏹ PARAR",
            font=("Segoe UI", 11, "bold"), bg="#d90429", fg="white",
            relief="raised", bd=2, width=11, pady=8, state="disabled",
            command=self.acao_parar
        )
        self.btn_parar.grid(row=0, column=1, padx=4)

        self.btn_mapear = tk.Button(
            btn_container, text="🎯 MAPEAR",
            font=("Segoe UI", 11, "bold"), bg="#ffb703", fg="#000000",
            relief="raised", bd=2, width=11, pady=8,
            command=self.acao_mapear_checklist
        )
        self.btn_mapear.grid(row=0, column=2, padx=4)

        # --- SEÇÃO 2: STATUS DA PLANILHA E CALIBRAÇÃO ---
        info_frame = tk.LabelFrame(
            main_frame, text=" Status de Configuração e Planilha ",
            font=("Segoe UI", 10, "bold"), bg="#2b3035", fg="#f8f9fa", padx=12, pady=10
        )
        info_frame.pack(fill="x", pady=(0, 12))

        # Linha Excel
        row_excel = tk.Frame(info_frame, bg="#2b3035")
        row_excel.pack(fill="x", pady=2)
        self.lbl_excel = tk.Label(
            row_excel, text="📊 Planilha: Verificando conferencia.xlsx...",
            font=("Segoe UI", 9), bg="#2b3035", fg="#ced4da"
        )
        self.lbl_excel.pack(side="left", fill="x", expand=True, anchor="w")
        tk.Button(
            row_excel, text="Selec...", font=("Segoe UI", 8), bg="#495057", fg="white",
            command=self.selecionar_planilha
        ).pack(side="right")

        # Linha Calibração
        self.lbl_calib = tk.Label(
            info_frame, text="📍 Mapeamento: Verificando coordenadas...",
            font=("Segoe UI", 9), bg="#2b3035", fg="#ced4da"
        )
        self.lbl_calib.pack(anchor="w", pady=(4, 2))

        # --- SEÇÃO ACOMPANHAMENTO FINANCEIRO AO VIVO ---
        soma_frame = tk.Frame(main_frame, bg="#1a1d20", bd=1, relief="ridge", pady=10, padx=14)
        soma_frame.pack(fill="x", pady=(0, 12))

        self.lbl_soma_total = tk.Label(
            soma_frame, text="💰 MARCADO GAM: R$ 0,00 / R$ 0,00",
            font=("Segoe UI", 11, "bold"), bg="#1a1d20", fg="#55a630"
        )
        self.lbl_soma_total.pack(side="left")

        self.lbl_soma_consinco = tk.Label(
            soma_frame, text=" 📊 TOTAL CONSINCO: R$ 0,00",
            font=("Segoe UI", 10, "bold"), bg="#1a1d20", fg="#ffb703"
        )
        self.lbl_soma_consinco.pack(side="left", padx=10)

        self.lbl_soma_itens = tk.Label(
            soma_frame, text="✔ Validados: 0 / 0",
            font=("Segoe UI", 10, "bold"), bg="#1a1d20", fg="#48cae4"
        )
        self.lbl_soma_itens.pack(side="right")

        # --- SEÇÃO 3: OPÇÕES AVANÇADAS (MODO DE LEITURA) ---
        opts_frame = tk.Frame(main_frame, bg="#212529")
        opts_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(opts_frame, text="Modo de Leitura na Tela:", font=("Segoe UI", 9, "bold"), bg="#212529", fg="#adb5bd").pack(side="left")
        self.var_modo = tk.StringVar(value="ocr")
        tk.Radiobutton(
            opts_frame, text="OCR Visual (Recomendado - Sem Ctrl+C)",
            variable=self.var_modo, value="ocr", bg="#212529", fg="#f8f9fa",
            selectcolor="#343a40", activebackground="#212529", activeforeground="#f8f9fa",
            command=self.alterar_modo_leitura
        ).pack(side="left", padx=8)
        tk.Radiobutton(
            opts_frame, text="Clipboard (Ctrl+C)",
            variable=self.var_modo, value="clipboard", bg="#212529", fg="#f8f9fa",
            selectcolor="#343a40", activebackground="#212529", activeforeground="#f8f9fa",
            command=self.alterar_modo_leitura
        ).pack(side="left")

        # --- SEÇÃO 4: LOG EM TEMPO REAL ---
        tk.Label(
            main_frame, text="📜 Log de Execução e Validação:",
            font=("Segoe UI", 10, "bold"), bg="#212529", fg="#f8f9fa"
        ).pack(anchor="w", pady=(0, 4))

        log_container = tk.Frame(main_frame, bg="#343a40")
        log_container.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_container)
        scrollbar.pack(side="right", fill="y")

        self.log_text = tk.Text(
            log_container, font=("Consolas", 9), bg="#181a1b", fg="#e8e6e3",
            yscrollcommand=scrollbar.set, state="disabled", wrap="word"
        )
        self.log_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Configuração de tags de cor para os logs
        self.log_text.tag_config("sucesso", foreground="#55a630")
        self.log_text.tag_config("erro", foreground="#ef233c")
        self.log_text.tag_config("aviso", foreground="#ffb703")
        self.log_text.tag_config("start", foreground="#00b4d8", font=("Consolas", 9, "bold"))
        self.log_text.tag_config("contagem", foreground="#f72585", font=("Consolas", 10, "bold"))

        # --- SEÇÃO 5: BARRA DE STATUS INFERIOR ---
        self.status_bar = tk.Label(
            self.root, text=" Status: Pronto para iniciar ",
            font=("Segoe UI", 9, "bold"), bg="#1a1d20", fg="#48cae4", anchor="w", padx=12, pady=6
        )
        self.status_bar.pack(fill="x", side="bottom")

    def log(self, mensagem: str):
        self.root.after(0, lambda: self._log_ui(mensagem))

    def _log_ui(self, mensagem: str):
        self.log_text.config(state="normal")
        timestamp = time.strftime('%H:%M:%S')
        texto_formatado = f"[{timestamp}] {mensagem}\n"
        
        tag = None
        if "✅" in mensagem or "VALIDADO" in mensagem or "[SUCESSO]" in mensagem:
            tag = "sucesso"
        elif "⚠️" in mensagem or "PULADO" in mensagem or "[AVISO]" in mensagem:
            tag = "aviso"
        elif "[ERRO" in mensagem or "❌" in mensagem:
            tag = "erro"
        elif "[START]" in mensagem or "INICIANDO" in mensagem:
            tag = "start"
        elif "[CONTAGEM]" in mensagem:
            tag = "contagem"

        if tag:
            self.log_text.insert(tk.END, texto_formatado, tag)
        else:
            self.log_text.insert(tk.END, texto_formatado)

        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def set_status(self, status: str):
        self.root.after(0, lambda: self._ui_status_update(status))

    def _ui_status_update(self, status: str):
        self.status_bar.config(text=f" Status: {status} ")
        self.update_summary_ui()

    def update_summary_ui(self, consinco_val=None):
        try:
            resumo = self.excel_manager.get_resumo()
            val_soma = resumo.get("valor_somado", 0.0)
            val_esperado = resumo.get("valor_total_esperado", 0.0)
            
            val_fmt = f"{val_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            esp_fmt = f"{val_esperado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            self.lbl_soma_total.config(text=f"💰 MARCADO GAM: R$ {val_fmt} / R$ {esp_fmt}")
            self.lbl_soma_itens.config(text=f"✔ Validados: {resumo.get('validados', 0)} / {resumo.get('total', 0)}")

            if consinco_val is not None:
                cons_fmt = f"{consinco_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                self.lbl_soma_consinco.config(text=f" 📊 TOTAL CONSINCO: R$ {cons_fmt}")
        except Exception:
            pass

    def alterar_modo_leitura(self):
        modo = self.var_modo.get()
        self.screen_reader.set_mode(modo)
        self.log(f"[CONFIG] Modo de leitura alterado para: {modo.upper()}")

    def check_initial_excel(self):
        caminhos_tentativa = [
            os.path.join(base_dir, "Dados", "conferencia.xlsx"),
            os.path.join(base_dir, "Dados", "conferencia.csv"),
            os.path.join(base_dir, "conferencia.xlsx"),
            os.path.join(base_dir, "conferencia.csv")
        ]
        caminho_alvo = None
        for c in caminhos_tentativa:
            if os.path.exists(c):
                caminho_alvo = c
                break

        if caminho_alvo:
            sucesso, msg = self.excel_manager.carregar_planilha(caminho_alvo)
            if sucesso:
                self.lbl_excel.config(text=f"📊 Planilha: {os.path.basename(caminho_alvo)} ({len(self.excel_manager.dados_sanitizados)} títulos)", fg="#55a630")
                self.log(f"[EXCEL] {msg}")
            else:
                self.lbl_excel.config(text=f"📊 Planilha erro: {msg}", fg="#ef233c")
                self.log(f"[ERRO EXCEL] {msg}")
        else:
            self.lbl_excel.config(text="📊 Planilha: Dados/conferencia.xlsx não encontrada", fg="#ffb703")
            self.log("[AVISO] Arquivo conferencia.xlsx não encontrado na pasta 'Dados'. Clique em 'Selec...' para escolher.")
        self.update_summary_ui()

    def selecionar_planilha(self):
        filepath = filedialog.askopenfilename(
            title="Selecione a tabela de conferência",
            filetypes=[("Arquivos Excel/CSV", "*.xlsx *.xls *.csv"), ("Todos os arquivos", "*.*")]
        )
        if filepath:
            sucesso, msg = self.excel_manager.carregar_planilha(filepath)
            if sucesso:
                self.lbl_excel.config(text=f"📊 Planilha: {os.path.basename(filepath)} ({len(self.excel_manager.dados_sanitizados)} títulos)", fg="#55a630")
                self.log(f"[EXCEL] {msg}")
            else:
                messagebox.showerror("Erro na Planilha", msg)
                self.lbl_excel.config(text=f"📊 Planilha inválida", fg="#ef233c")
        self.update_summary_ui()

    def update_calibration_status(self):
        path = get_coords_filepath()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    coords = json.load(f)
                linhas_y = coords.get("linhas_y", [])
                has_titulo = coords.get("x_titulo_esq") is not None
                has_vlr_lateral = coords.get("x_vlr_lateral") is not None
                has_total = coords.get("x_total_esq") is not None
                if len(linhas_y) == 12 and abs(linhas_y[11] - linhas_y[0]) < 80:
                    self.lbl_calib.config(text=f"📍 Mapeamento: Inválido (Linhas muito próximas: {abs(linhas_y[11]-linhas_y[0])}px. Recalibre!)", fg="#ef233c")
                elif has_titulo and has_vlr_lateral and has_total and coords.get("x_checkbox") and len(linhas_y) == 12:
                    self.lbl_calib.config(text="📍 Mapeamento: Completo (Tudo OK!)", fg="#55a630")
                elif has_titulo and coords.get("x_checkbox"):
                    self.lbl_calib.config(text="📍 Mapeamento: Faltam Passos 2 ou 5 (Recalibre!)", fg="#ffb703")
                else:
                    self.lbl_calib.config(text="📍 Mapeamento: Pendente (Clique em 'Mapear Checklist')", fg="#ffb703")
                return
            except Exception:
                pass
        self.lbl_calib.config(text="📍 Mapeamento: Pendente (Clique em 'Mapear Checklist')", fg="#ffb703")

    def acao_mapear_checklist(self):
        # Abre a janela de calibração passando callback para atualizar status ao salvar
        CalibradorChecklist(self.root, on_save_callback=lambda coords: self.update_calibration_status())

    def acao_comecar(self):
        if self.runner.is_running:
            return

        # Validações antes de iniciar
        if not self.excel_manager.dados_sanitizados:
            sucesso, msg = self.excel_manager.carregar_planilha()
            if not sucesso:
                messagebox.showwarning("Planilha Ausente", "Por favor, selecione ou coloque o arquivo 'conferencia.xlsx' na pasta do executável.")
                return

        path_coords = get_coords_filepath()
        if not os.path.exists(path_coords):
            messagebox.showwarning("Calibração Necessária", "Você deve clicar no botão 'Mapear Checklist' e capturar as coordenadas antes de começar.")
            return

        try:
            with open(path_coords, 'r', encoding='utf-8') as f:
                coords_check = json.load(f)
            if coords_check.get("x_titulo_esq") is None or coords_check.get("x_vlr_lateral") is None or coords_check.get("x_total_esq") is None:
                msg_alerta = (
                    "O arquivo de coordenadas atual está desatualizado.\n\n"
                    "Agora o Passo 2 é o clique único no 'Vlr Pagar/Rec Lateral', e o Passo 5 é o Total.\n\n"
                    "👉 Clique em 'Mapear Checklist' e refaça a calibração completando todos os 5 passos!"
                )
                messagebox.showwarning("Recalibração Necessária", msg_alerta)
                return
        except Exception:
            pass

        self.btn_comecar.config(state="disabled", bg="#6c757d")
        self.btn_mapear.config(state="disabled")
        self.btn_parar.config(state="normal", bg="#ef233c")

        self.runner.executar(
            log_cb=self.log,
            status_cb=self.set_status,
            finish_cb=self._on_finished,
            ask_cb=self.ask_round_continue,
            ask_divergencia_cb=self.ask_divergencia,
            update_consinco_cb=lambda val: self.root.after(0, lambda: self.update_summary_ui(val))
        )

    def ask_round_continue(self, rodada: int) -> bool:
        import threading
        evento = threading.Event()
        resultado = [None]
        self.root.after(0, lambda: self.popup_fim_rodada(evento, resultado, rodada))
        evento.wait()
        return resultado[0] == "continuar"

    def popup_fim_rodada(self, evento_conclusao, resultado, rodada):
        popup = tk.Toplevel(self.root)
        popup.title(f"Rodada {rodada} Concluída")
        popup.geometry("380x180")
        popup.attributes("-topmost", True)
        popup.configure(bg="#212529")
        
        # Centraliza o popup
        popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (380 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (180 // 2)
        popup.geometry(f"+{x}+{y}")
        
        lbl_msg = tk.Label(popup, text=f"Rodada {rodada} finalizada.\nDeseja continuar a execução?", font=("Segoe UI", 12, "bold"), bg="#212529", fg="#f8f9fa")
        lbl_msg.pack(pady=(20, 5))
        
        lbl_timer = tk.Label(popup, text="Continuando automaticamente em 10s...", font=("Segoe UI", 10), bg="#212529", fg="#ffb703")
        lbl_timer.pack()
        
        tempo_restante = 10
        timer_id = None
        
        def fechar(resp):
            nonlocal timer_id
            if timer_id:
                popup.after_cancel(timer_id)
            resultado[0] = resp
            popup.destroy()
            evento_conclusao.set()

        def atualizar_timer():
            nonlocal tempo_restante, timer_id
            tempo_restante -= 1
            if tempo_restante > 0:
                lbl_timer.config(text=f"Continuando automaticamente em {tempo_restante}s...")
                timer_id = popup.after(1000, atualizar_timer)
            else:
                fechar("continuar")

        btn_frame = tk.Frame(popup, bg="#212529")
        btn_frame.pack(pady=15)
        
        btn_cont = tk.Button(btn_frame, text="▶ Continuar", bg="#2b9348", fg="white", font=("Segoe UI", 10, "bold"), width=12, command=lambda: fechar("continuar"))
        btn_cont.pack(side="left", padx=10)
        
        btn_parar = tk.Button(btn_frame, text="⏹ Parar", bg="#d90429", fg="white", font=("Segoe UI", 10, "bold"), width=12, command=lambda: fechar("parar"))
        btn_parar.pack(side="right", padx=10)
        
        timer_id = popup.after(1000, atualizar_timer)

    def ask_divergencia(self, val_gam: float, val_cons: float) -> bool:
        import threading
        evento = threading.Event()
        resultado = [None]
        self.root.after(0, lambda: self.popup_divergencia(evento, resultado, val_gam, val_cons))
        evento.wait()
        return resultado[0] == "continuar"

    def popup_divergencia(self, evento_conclusao, resultado, val_gam, val_cons):
        popup = tk.Toplevel(self.root)
        popup.title("Divergência de Totais!")
        popup.geometry("450x220")
        popup.attributes("-topmost", True)
        popup.configure(bg="#212529")
        
        popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (450 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (220 // 2)
        popup.geometry(f"+{x}+{y}")
        
        v_gam_f = f"{val_gam:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        v_cons_f = f"{val_cons:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        lbl_msg = tk.Label(popup, text=f"DIVERGÊNCIA DETECTADA!\n\nSoma no GAM: R$ {v_gam_f}\nTotal Consinco: R$ {v_cons_f}", font=("Segoe UI", 11, "bold"), bg="#212529", fg="#ffb703")
        lbl_msg.pack(pady=(15, 5))
        
        lbl_q = tk.Label(popup, text="Deseja forçar a continuação?", font=("Segoe UI", 10), bg="#212529", fg="#f8f9fa")
        lbl_q.pack(pady=(5, 15))
        
        def fechar(resp):
            resultado[0] = resp
            popup.destroy()
            evento_conclusao.set()

        btn_frame = tk.Frame(popup, bg="#212529")
        btn_frame.pack()
        
        btn_cont = tk.Button(btn_frame, text="⚠️ Ignorar e Continuar", bg="#ffb703", fg="black", font=("Segoe UI", 9, "bold"), width=20, command=lambda: fechar("continuar"))
        btn_cont.pack(side="left", padx=10)
        
        btn_parar = tk.Button(btn_frame, text="⏹ Parar Execução", bg="#d90429", fg="white", font=("Segoe UI", 9, "bold"), width=15, command=lambda: fechar("parar"))
        btn_parar.pack(side="right", padx=10)

    def acao_parar(self):
        if self.runner.is_running:
            self.log("[SINAL] Enviando comando para parar execução...")
            self.set_status("Interrompendo...")
            self.runner.parar()

    def _on_finished(self):
        self.root.after(0, self._restore_buttons)

    def _restore_buttons(self):
        self.btn_comecar.config(state="normal", bg="#2b9348")
        self.btn_mapear.config(state="normal")
        self.btn_parar.config(state="disabled", bg="#6c757d")
        self.set_status("Pronto")
        self.update_calibration_status()
        self.update_summary_ui()


def main():
    root = tk.Tk()
    app = MiniGamApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
