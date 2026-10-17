# -*- coding: utf-8 -*-
"""
==============================================================================
PAINEL DE APOIO OPERACIONAL - CENTRAL DE AUTOMAÇÕES E CONSULTAS
==============================================================================
Interface gráfica desenvolvida nos mesmos padrões visuais do GAM (Tkinter).

Ações integradas:
1. Executar '1-data_query.py' (import_querys)
2. Executar '1-min_max.py' (min_e_max) com parâmetros solicitados graficamente
   e abertura automática de 'ajustepp.xlsx' ao terminar
3. Abrir 'capacidade.xlsx' (min_e_max) diretamente no Excel
==============================================================================
"""

import os
import re
import sys
import time
import queue
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Som no Windows
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class PainelApoioApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Painel de Apoio - Automações & Relatórios")
        self.root.geometry("680x920")
        self.root.minsize(620, 750)
        self.root.configure(bg="#f0f0f0")
        
        # Padrão semelhante ao GAM: Manter sobre as outras janelas (com opção de desmarcar)
        self.topmost_var = tk.BooleanVar(value=True)
        self.root.attributes("-topmost", self.topmost_var.get())

        # Resolução dos diretórios do ecossistema
        self.base_dir = Path(__file__).resolve().parent
        self.aplicativos_dir = self.base_dir.parent

        self.path_data_query = self.aplicativos_dir / "import_querys" / "1-data_query.py"
        self.path_min_max = self.aplicativos_dir / "min_e_max" / "1-min_max.py"
        self.path_capacidade = self.aplicativos_dir / "min_e_max" / "capacidade.xlsx"
        self.path_gam = self.aplicativos_dir / "GAM" / "gam.py"

        # Possíveis caminhos do arquivo de saída ajustepp.xlsx
        self.path_ajustepp_gam = self.aplicativos_dir / "GAM" / "bd_entrada" / "ajustepp.xlsx"
        self.path_ajustepp_minmax = self.aplicativos_dir / "min_e_max" / "ajustepp.xlsx"

        # Caminhos da planilha de digitar (GAM/bd_saida)
        self.path_digitar = self.aplicativos_dir / "GAM" / "bd_saida" / "digitar.xlsx"
        self.path_digitar_csv = self.aplicativos_dir / "GAM" / "bd_saida" / "digitar.csv"

        # Controle de concorrência e processo
        self.current_process = None
        self.is_running = False
        self.stop_requested = False
        self.queue = queue.Queue()

        self.criar_estilos()
        self.criar_widgets()

        # Inicia loop de leitura da fila de logs
        self.root.after(100, self.processar_fila)

        # Hook para fechar com segurança
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)

        # Log de inicialização
        self.log("Painel de Apoio carregado e pronto para uso.", "INFO")
        self.verificar_arquivos_iniciais()

    def criar_estilos(self):
        """Configura estilos ttk e cores base."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TProgressbar", thickness=8)

    def criar_widgets(self):
        """Monta a estrutura visual idêntica ao design system do GAM."""
        # =====================================================================
        # 1. CABEÇALHO SUPERIOR
        # =====================================================================
        header_frame = tk.Frame(self.root, bg="#203354", padx=15, pady=12)
        header_frame.pack(fill="x", side="top")

        title_box = tk.Frame(header_frame, bg="#203354")
        title_box.pack(side="left", fill="both", expand=True)

        lbl_titulo = tk.Label(
            title_box,
            text="PAINEL DE APOIO OPERACIONAL",
            font=("Segoe UI", 13, "bold"),
            fg="#ffffff",
            bg="#203354",
            anchor="w"
        )
        lbl_titulo.pack(fill="x")

        lbl_subtitulo = tk.Label(
            title_box,
            text="Central Integrada: Import Querys • Mínimo/Máximo • Capacidade",
            font=("Segoe UI", 9),
            fg="#b0c4de",
            bg="#203354",
            anchor="w"
        )
        lbl_subtitulo.pack(fill="x", pady=(2, 0))

        chk_topmost = tk.Checkbutton(
            header_frame,
            text="Sempre no topo",
            variable=self.topmost_var,
            command=self.toggle_topmost,
            font=("Segoe UI", 9),
            fg="#ffffff",
            bg="#203354",
            activebackground="#203354",
            activeforeground="#ffffff",
            selectcolor="#102030"
        )
        chk_topmost.pack(side="right")

        # =====================================================================
        # 2. CONTAINER PRINCIPAL DE BOTÕES / AÇÕES
        # =====================================================================
        content_frame = tk.Frame(self.root, bg="#f0f0f0", padx=14, pady=10)
        content_frame.pack(fill="x")

        # --- AÇÃO 1: 1-data_query.py ---
        card_query = tk.LabelFrame(
            content_frame,
            text=" 1. Importação & Tratamento de Dados ",
            font=("Segoe UI", 9, "bold"),
            bg="#f0f0f0",
            fg="#1a365d",
            padx=10,
            pady=8
        )
        card_query.pack(fill="x", pady=(0, 8))

        lbl_query_desc = tk.Label(
            card_query,
            text="Processa 'query.txt', gera o 'query.parquet' e sincroniza com o AppSheet/banco de dados.",
            font=("Segoe UI", 8),
            fg="#555555",
            bg="#f0f0f0",
            justify="left",
            anchor="w"
        )
        lbl_query_desc.pack(fill="x", pady=(0, 5))

        self.btn_exec_query = tk.Button(
            card_query,
            text="▶ Executar Data Query (1-data_query.py)",
            command=self.acao_executar_data_query,
            bg="#1976D2",
            fg="white",
            activebackground="#1565C0",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="raised",
            bd=2,
            cursor="hand2",
            pady=6
        )
        self.btn_exec_query.pack(fill="x")

        # --- AÇÃO 2: 1-min_max.py + parâmetros gráficos + abrir ajustepp.xlsx ---
        card_minmax = tk.LabelFrame(
            content_frame,
            text=" 2. Cálculo de Estoque Mínimo e Máximo (Com Parâmetros Gráficos) ",
            font=("Segoe UI", 9, "bold"),
            bg="#f0f0f0",
            fg="#1b5e20",
            padx=10,
            pady=8
        )
        card_minmax.pack(fill="x", pady=(0, 8))

        lbl_minmax_desc = tk.Label(
            card_minmax,
            text="Solicita escopo e filtros graficamente, calcula e abre automaticamente a planilha de digitar e o resultado.",
            font=("Segoe UI", 8),
            fg="#555555",
            bg="#f0f0f0",
            justify="left",
            anchor="w"
        )
        lbl_minmax_desc.pack(fill="x", pady=(0, 5))

        self.btn_exec_minmax = tk.Button(
            card_minmax,
            text="▶ Configurar & Executar Mín/Máx (1-min_max.py)",
            command=self.acao_executar_min_max,
            bg="#2E7D32",
            fg="white",
            activebackground="#1B5E20",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="raised",
            bd=2,
            cursor="hand2",
            pady=6
        )
        self.btn_exec_minmax.pack(fill="x")

        # --- AÇÃO 3: Abrir capacidade.xlsx ---
        card_capacidade = tk.LabelFrame(
            content_frame,
            text=" 3. Planilha de Capacidade ",
            font=("Segoe UI", 9, "bold"),
            bg="#f0f0f0",
            fg="#e65100",
            padx=10,
            pady=8
        )
        card_capacidade.pack(fill="x", pady=(0, 8))

        lbl_cap_desc = tk.Label(
            card_capacidade,
            text="Abre a planilha oficial 'capacidade.xlsx' diretamente no Excel para consulta e parametrização.",
            font=("Segoe UI", 8),
            fg="#555555",
            bg="#f0f0f0",
            justify="left",
            anchor="w"
        )
        lbl_cap_desc.pack(fill="x", pady=(0, 5))

        self.btn_abrir_capacidade = tk.Button(
            card_capacidade,
            text="📊 Abrir Planilha de Capacidade (capacidade.xlsx)",
            command=self.acao_abrir_capacidade,
            bg="#EF6C00",
            fg="white",
            activebackground="#D84315",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="raised",
            bd=2,
            cursor="hand2",
            pady=6
        )
        self.btn_abrir_capacidade.pack(fill="x")

        # --- AÇÃO 4: Abrir GAM e Fechar Apoio ---
        card_gam = tk.LabelFrame(
            content_frame,
            text=" 4. Gerenciador de Automações (GAM) ",
            font=("Segoe UI", 9, "bold"),
            bg="#f0f0f0",
            fg="#4a148c",
            padx=10,
            pady=8
        )
        card_gam.pack(fill="x", pady=(0, 8))

        lbl_gam_desc = tk.Label(
            card_gam,
            text="Executa o GAM (gam.py) em processo independente e encerra automaticamente este Painel de Apoio.",
            font=("Segoe UI", 8),
            fg="#555555",
            bg="#f0f0f0",
            justify="left",
            anchor="w"
        )
        lbl_gam_desc.pack(fill="x", pady=(0, 5))

        self.btn_abrir_gam = tk.Button(
            card_gam,
            text="🚀 Abrir GAM (gam.py) e Fechar Painel de Apoio",
            command=self.acao_abrir_gam_e_fechar,
            bg="#5E35B1",
            fg="white",
            activebackground="#4527A0",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="raised",
            bd=2,
            cursor="hand2",
            pady=6
        )
        self.btn_abrir_gam.pack(fill="x")

        # =====================================================================
        # 3. BARRA DE CONTROLE DA EXECUÇÃO ATIVA
        # =====================================================================
        ctrl_frame = tk.Frame(content_frame, bg="#f0f0f0")
        ctrl_frame.pack(fill="x", pady=(2, 0))

        self.lbl_status = tk.Label(
            ctrl_frame,
            text="Status: Sistema pronto para execução.",
            font=("Segoe UI", 9, "bold"),
            fg="#333333",
            bg="#f0f0f0",
            anchor="w"
        )
        self.lbl_status.pack(side="left", fill="x", expand=True)

        self.btn_parar = tk.Button(
            ctrl_frame,
            text="⏹ PARAR PROCESSO",
            command=self.parar_execucao_atual,
            state="disabled",
            bg="#cccccc",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="raised",
            bd=1,
            padx=12,
            pady=3
        )
        self.btn_parar.pack(side="right")

        self.progress = ttk.Progressbar(content_frame, mode="indeterminate", style="TProgressbar")
        self.progress.pack(fill="x", pady=(6, 0))

        # =====================================================================
        # 4. PAINEL DE LOGS (Estilo GAM com timestamps e tags coloridas)
        # =====================================================================
        log_frame = tk.Frame(self.root, bg="#f0f0f0", padx=14, pady=8)
        log_frame.pack(fill="both", expand=True)

        log_header = tk.Frame(log_frame, bg="#f0f0f0")
        log_header.pack(fill="x", pady=(0, 4))

        tk.Label(
            log_header,
            text="Log de Execução em Tempo Real:",
            font=("Segoe UI", 9, "bold"),
            bg="#f0f0f0"
        ).pack(side="left")

        btn_limpar = tk.Button(
            log_header,
            text="Limpar Log",
            command=self.limpar_log,
            font=("Segoe UI", 8),
            bg="#e0e0e0",
            relief="flat",
            padx=8,
            pady=1,
            cursor="hand2"
        )
        btn_limpar.pack(side="right", padx=(4, 0))

        btn_abrir_pasta = tk.Button(
            log_header,
            text="Abrir Pasta Apoio",
            command=self.abrir_pasta_apoio,
            font=("Segoe UI", 8),
            bg="#e0e0e0",
            relief="flat",
            padx=8,
            pady=1,
            cursor="hand2"
        )
        btn_abrir_pasta.pack(side="right")

        # Área de texto do log
        log_container = tk.Frame(log_frame, bg="#ffffff", bd=1, relief="solid")
        log_container.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_container,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            wrap="word",
            state="disabled",
            bd=0
        )
        scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # Barra de Resposta Interativa ao Terminal (Entrada ao vivo para qualquer prompt)
        interactive_bar = tk.Frame(log_frame, bg="#f0f0f0", pady=4)
        interactive_bar.pack(fill="x")

        tk.Label(
            interactive_bar,
            text="Entrada Terminal:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0f0f0",
            fg="#444444"
        ).pack(side="left", padx=(0, 4))

        self.entry_terminal = tk.Entry(
            interactive_bar,
            font=("Consolas", 9),
            state="disabled",
            bg="#ffffff"
        )
        self.entry_terminal.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.entry_terminal.bind("<Return>", lambda event: self.enviar_para_terminal())

        self.btn_enviar_terminal = tk.Button(
            interactive_bar,
            text="Enviar (Enter)",
            command=self.enviar_para_terminal,
            state="disabled",
            bg="#cccccc",
            fg="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=8,
            pady=1
        )
        self.btn_enviar_terminal.pack(side="right")

        # Configuração de cores e estilos para tags de log
        self.log_text.tag_configure("INFO", foreground="#61afef")
        self.log_text.tag_configure("SUCCESS", foreground="#98c379")
        self.log_text.tag_configure("WARNING", foreground="#e5c07b")
        self.log_text.tag_configure("ERROR", foreground="#e06c75")
        self.log_text.tag_configure("PROMPT", foreground="#c678dd")
        self.log_text.tag_configure("TIMESTAMP", foreground="#7f848e")
        self.log_text.tag_configure("DEFAULT", foreground="#abb2bf")

    def toggle_topmost(self):
        """Alterna se a janela fica sempre sobreposta."""
        self.root.attributes("-topmost", self.topmost_var.get())

    def verificar_arquivos_iniciais(self):
        """Verifica se os arquivos e scripts esperados existem no workspace."""
        for label, path in [
            ("1-data_query.py", self.path_data_query),
            ("1-min_max.py", self.path_min_max),
            ("capacidade.xlsx", self.path_capacidade),
            ("digitar.xlsx", self.path_digitar),
            ("gam.py", self.path_gam)
        ]:
            if not path.exists():
                self.log(f"[AVISO] Arquivo não localizado: {path}", "WARNING")
            else:
                self.log(f"[OK] Vinculado com sucesso: {label} -> {path.name}", "SUCCESS")

    def log(self, mensagem: str, nivel: str = "DEFAULT"):
        """Escreve uma linha formatada na área de texto do log."""
        self.log_text.config(state="normal")
        hora = time.strftime("%H:%M:%S")

        self.log_text.insert(tk.END, f"[{hora}] ", "TIMESTAMP")

        tag_to_apply = "DEFAULT"
        if nivel in ("INFO", "SUCCESS", "WARNING", "ERROR", "PROMPT"):
            tag_to_apply = nivel
        elif "[OK]" in mensagem or "[SUCESSO]" in mensagem:
            tag_to_apply = "SUCCESS"
        elif "[ERRO]" in mensagem or "Erro:" in mensagem or "Exception" in mensagem:
            tag_to_apply = "ERROR"
        elif "[AVISO]" in mensagem or "[ALERTA]" in mensagem or "Aviso:" in mensagem:
            tag_to_apply = "WARNING"
        elif "->" in mensagem or "Digite a opção" in mensagem or "Digite o número" in mensagem:
            tag_to_apply = "PROMPT"

        self.log_text.insert(tk.END, f"{mensagem}\n", tag_to_apply)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def limpar_log(self):
        """Limpa a área de texto de logs."""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")
        self.log("Log limpo pelo usuário.", "INFO")

    def abrir_pasta_apoio(self):
        """Abre a pasta local no Windows Explorer."""
        try:
            os.startfile(str(self.base_dir))
        except Exception as e:
            self.log(f"Erro ao abrir pasta: {e}", "ERROR")

    def atualizar_estado_botoes(self):
        """Habilita ou desabilita botões conforme o estado de execução."""
        if self.is_running:
            self.btn_exec_query.config(state="disabled", bg="#cccccc", cursor="arrow")
            self.btn_exec_minmax.config(state="disabled", bg="#cccccc", cursor="arrow")
            self.btn_abrir_capacidade.config(state="disabled", bg="#cccccc", cursor="arrow")
            self.btn_abrir_gam.config(state="disabled", bg="#cccccc", cursor="arrow")
            self.btn_parar.config(state="normal", bg="#FF5252", cursor="hand2")
            
            # Habilita barra de entrada terminal
            self.entry_terminal.config(state="normal", bg="#ffffff")
            self.btn_enviar_terminal.config(state="normal", bg="#203354", cursor="hand2")
            
            self.progress.start(10)
        else:
            self.btn_exec_query.config(state="normal", bg="#1976D2", cursor="hand2")
            self.btn_exec_minmax.config(state="normal", bg="#2E7D32", cursor="hand2")
            self.btn_abrir_capacidade.config(state="normal", bg="#EF6C00", cursor="hand2")
            self.btn_abrir_gam.config(state="normal", bg="#5E35B1", cursor="hand2")
            self.btn_parar.config(state="disabled", bg="#cccccc", cursor="arrow")
            
            # Desabilita barra de entrada terminal
            self.entry_terminal.delete(0, tk.END)
            self.entry_terminal.config(state="disabled", bg="#f4f4f4")
            self.btn_enviar_terminal.config(state="disabled", bg="#cccccc", cursor="arrow")
            
            self.progress.stop()

    def enviar_para_terminal(self):
        """Envia texto digitado na barra de terminal ao processo em execução."""
        if not self.is_running or not self.current_process or not self.current_process.stdin:
            return

        texto = self.entry_terminal.get().strip()
        if not texto:
            return

        try:
            self.current_process.stdin.write(f"{texto}\n")
            self.current_process.stdin.flush()
            self.log(f">>> Resposta enviada ao terminal: {texto}", "INFO")
            self.entry_terminal.delete(0, tk.END)
        except Exception as e:
            self.log(f"[ERRO] Falha ao enviar para o terminal: {e}", "ERROR")

    def tocar_som_notificacao(self):
        """Emite alerta sonoro suave como no GAM."""
        if HAS_WINSOUND:
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                pass

    # =========================================================================
    # AÇÕES DOS BOTÕES
    # =========================================================================
    def acao_executar_data_query(self):
        """1º Botão: Executa 1-data_query.py em segundo plano."""
        if self.is_running:
            messagebox.showwarning("Aviso", "Já existe uma automação em andamento.")
            return

        if not self.path_data_query.exists():
            msg = f"Arquivo não encontrado:\n{self.path_data_query}"
            messagebox.showerror("Erro de Arquivo", msg)
            self.log(f"[ERRO] {msg}", "ERROR")
            return

        self.iniciar_subprocesso(
            script_path=self.path_data_query,
            titulo="Data Query (1-data_query.py)",
            ao_finalizar_callback=None
        )

    def acao_executar_min_max(self):
        """2º Botão: Solicita parâmetros graficamente e executa 1-min_max.py."""
        if self.is_running:
            messagebox.showwarning("Aviso", "Já existe uma automação em andamento.")
            return

        if not self.path_min_max.exists():
            msg = f"Arquivo não encontrado:\n{self.path_min_max}"
            messagebox.showerror("Erro de Arquivo", msg)
            self.log(f"[ERRO] {msg}", "ERROR")
            return

        # Abre a janela modal para coletar as interações solicitadas pelo terminal
        self.abrir_dialogo_parametros_min_max()

    def abrir_dialogo_parametros_min_max(self):
        """
        Janela modal que substitui graficamente as perguntas de terminal do 1-min_max.py:
        1. Escopo de Lojas: 1 (Todas) ou 2 (Loja Específica com número da loja)
        2. Opção de Exportação: 1 (Aumentar), 2 (Total), 3 (Diminuir), 4 (Ambos extremos)
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Parâmetros do Mínimo e Máximo")
        dialog.geometry("560x530")
        dialog.resizable(False, False)
        dialog.configure(bg="#f0f0f0")
        dialog.attributes("-topmost", True)
        dialog.transient(self.root)
        dialog.grab_set()

        # Centraliza a modal na tela
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 280
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 265
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

        # Cabeçalho da Janela Modal
        header = tk.Frame(dialog, bg="#203354", padx=12, pady=10)
        header.pack(fill="x")
        tk.Label(
            header,
            text="DEFINIÇÃO DE PARÂMETROS DO CÁLCULO",
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg="#203354"
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Configure as opções abaixo para iniciar a execução sem digitar no terminal.",
            font=("Segoe UI", 8),
            fg="#b0c4de",
            bg="#203354"
        ).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(dialog, bg="#f0f0f0", padx=14, pady=10)
        body.pack(fill="both", expand=True)

        # --- GRUPO 1: ESCOPO DE PROCESSAMENTO ---
        frame_escopo = tk.LabelFrame(
            body,
            text=" 1. Escopo de Lojas (Primeira Interação) ",
            font=("Segoe UI", 9, "bold"),
            bg="#f0f0f0",
            fg="#1a365d",
            padx=10,
            pady=8
        )
        frame_escopo.pack(fill="x", pady=(0, 10))

        escopo_var = tk.StringVar(value="1")
        loja_var = tk.StringVar(value="")

        def atualizar_estado_loja():
            if escopo_var.get() == "2":
                entry_loja.config(state="normal", bg="#ffffff")
                entry_loja.focus_set()
            else:
                entry_loja.config(state="disabled", bg="#e8e8e8")

        rb_todas = tk.Radiobutton(
            frame_escopo,
            text="[1] Todas as Lojas da Rede (Geral - exceto CDs)",
            variable=escopo_var,
            value="1",
            command=atualizar_estado_loja,
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            activebackground="#f0f0f0"
        )
        rb_todas.pack(anchor="w", pady=2)

        frame_loja_especifica = tk.Frame(frame_escopo, bg="#f0f0f0")
        frame_loja_especifica.pack(anchor="w", fill="x", pady=2)

        rb_especifica = tk.Radiobutton(
            frame_loja_especifica,
            text="[2] Loja(s) Específica(s) (Processamento Exclusivo)",
            variable=escopo_var,
            value="2",
            command=atualizar_estado_loja,
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            activebackground="#f0f0f0"
        )
        rb_especifica.pack(anchor="w")

        f_input_loja = tk.Frame(frame_loja_especifica, bg="#f0f0f0")
        f_input_loja.pack(anchor="w", fill="x", padx=(24, 0), pady=(2, 0))

        lbl_loja = tk.Label(f_input_loja, text="Loja(s):", font=("Segoe UI", 9, "bold"), bg="#f0f0f0")
        lbl_loja.pack(side="left", padx=(0, 4))

        entry_loja = tk.Entry(f_input_loja, textvariable=loja_var, width=28, font=("Segoe UI", 9), state="disabled", bg="#e8e8e8")
        entry_loja.pack(side="left")

        lbl_hint = tk.Label(f_input_loja, text=" (ex: 01, 02, 03 ou 14, 18)", font=("Segoe UI", 8, "italic"), fg="#777777", bg="#f0f0f0")
        lbl_hint.pack(side="left", padx=(4, 0))

        # --- GRUPO 2: TIPO DE RELATÓRIO / EXPORTAÇÃO ---
        frame_relatorio = tk.LabelFrame(
            body,
            text=" 2. Filtro de Relatório / Exportação (Segunda Interação) ",
            font=("Segoe UI", 9, "bold"),
            bg="#f0f0f0",
            fg="#1b5e20",
            padx=10,
            pady=8
        )
        frame_relatorio.pack(fill="x", pady=(0, 10))

        relatorio_var = tk.StringVar(value="1")

        opcoes_rel = [
            ("1", "[1] APENAS sugestões para AUMENTAR (Recomendado)", "Filtra casos onde o Novo Mínimo Calculado é maior que o Atual."),
            ("2", "[2] TOTAL", "Exporta a base completa, englobando altas e baixas com alteração."),
            ("3", "[3] APENAS sugestões para DIMINUIR", "Filtra casos onde o Novo Mínimo Calculado é menor que o Atual."),
            ("4", "[4] APENAS AUMENTOS e REDUÇÕES", "Filtra alterações no Mínimo, ignorando se apenas o Máximo mudou.")
        ]

        for val, titulo, desc in opcoes_rel:
            f_op = tk.Frame(frame_relatorio, bg="#f0f0f0")
            f_op.pack(anchor="w", fill="x", pady=2)

            rb = tk.Radiobutton(
                f_op,
                text=titulo,
                variable=relatorio_var,
                value=val,
                font=("Segoe UI", 9, "bold" if val == "1" else "normal"),
                bg="#f0f0f0",
                activebackground="#f0f0f0"
            )
            rb.pack(anchor="w")

            lbl_desc = tk.Label(
                f_op,
                text=f"      {desc}",
                font=("Segoe UI", 8),
                fg="#666666",
                bg="#f0f0f0"
            )
            lbl_desc.pack(anchor="w")

        # --- BOTÕES DE AÇÃO DO DIÁLOGO ---
        btn_frame = tk.Frame(dialog, bg="#e0e0e0", padx=14, pady=10)
        btn_frame.pack(fill="x", side="bottom")

        def confirmar():
            escopo = escopo_var.get()
            loja_num = loja_var.get().strip()
            relatorio = relatorio_var.get()

            lojas_selecionadas = []
            if escopo == "2":
                lojas_encontradas = [int(num) for num in re.findall(r'\d+', loja_num) if int(num) > 0]
                lojas_selecionadas = list(dict.fromkeys(lojas_encontradas))
                if not lojas_selecionadas:
                    messagebox.showerror(
                        "Loja(s) Inválida(s)",
                        "Por favor, informe ao menos uma loja válida maior que 0 (ex: 01, 02, 03 ou 14, 18).",
                        parent=dialog
                    )
                    entry_loja.focus_set()
                    return

            # Monta a sequência de respostas que o terminal do 1-min_max.py espera
            if escopo == "1":
                stdin_payload = f"1\n{relatorio}\n"
                desc_escopo = "Todas as Lojas (Geral)"
            else:
                lojas_formatadas = [f"{l:02d}" if l < 10 else str(l) for l in lojas_selecionadas]
                lojas_str = ", ".join(lojas_formatadas)
                stdin_payload = f"2\n{lojas_str}\n{relatorio}\n"
                desc_escopo = f"Loja(s) Específica(s): {lojas_str}"

            dialog.destroy()

            self.log("------------------------------------------------------------", "INFO")
            self.log(f"[PARÂMETROS DEFINIDOS GRAFICAMENTE]", "INFO")
            self.log(f"-> Escopo: {desc_escopo}", "INFO")
            self.log(f"-> Opção de Relatório: Opção [{relatorio}]", "INFO")
            self.log("------------------------------------------------------------", "INFO")

            # Dispara o subprocesso alimentando as entradas automaticamente
            self.iniciar_subprocesso(
                script_path=self.path_min_max,
                titulo="Mínimo e Máximo (1-min_max.py)",
                ao_finalizar_callback=self.abrir_planilhas_pos_min_max,
                stdin_data=stdin_payload
            )

        btn_cancelar = tk.Button(
            btn_frame,
            text="Cancelar",
            command=dialog.destroy,
            font=("Segoe UI", 9),
            bg="#f5f5f5",
            relief="raised",
            bd=1,
            padx=14,
            pady=4,
            cursor="hand2"
        )
        btn_cancelar.pack(side="right", padx=(8, 0))

        btn_confirmar = tk.Button(
            btn_frame,
            text="▶ Confirmar e Iniciar Cálculo",
            command=confirmar,
            font=("Segoe UI", 9, "bold"),
            bg="#2E7D32",
            fg="white",
            activebackground="#1B5E20",
            activeforeground="white",
            relief="raised",
            bd=2,
            padx=16,
            pady=4,
            cursor="hand2"
        )
        btn_confirmar.pack(side="right")

    def acao_abrir_capacidade(self):
        """3º Botão: Abre diretamente o arquivo capacidade.xlsx."""
        if not self.path_capacidade.exists():
            msg = f"Arquivo de capacidade não encontrado:\n{self.path_capacidade}"
            messagebox.showerror("Arquivo Inexistente", msg)
            self.log(f"[ERRO] {msg}", "ERROR")
            return

        try:
            self.log(f"Abrindo planilha de capacidade: {self.path_capacidade.name}...", "INFO")
            os.startfile(str(self.path_capacidade))
            self.log(f"[SUCESSO] Planilha 'capacidade.xlsx' aberta com sucesso!", "SUCCESS")
            self.tocar_som_notificacao()
        except Exception as e:
            err = f"Falha ao abrir capacidade.xlsx: {e}"
            messagebox.showerror("Erro ao Abrir", err)
            self.log(f"[ERRO] {err}", "ERROR")

    def acao_abrir_gam_e_fechar(self):
        """4º Botão: Executa o GAM (gam.py) em processo independente e encerra o Painel de Apoio."""
        if not self.path_gam.exists():
            msg = f"Arquivo do GAM não encontrado:\n{self.path_gam}"
            messagebox.showerror("Arquivo Inexistente", msg)
            self.log(f"[ERRO] {msg}", "ERROR")
            return

        if self.is_running:
            resp = messagebox.askyesno(
                "Processo em Execução",
                "Existe uma automação rodando no momento. Deseja realmente interromper o processo atual, abrir o GAM e fechar o Painel de Apoio?"
            )
            if not resp:
                return
            if self.current_process:
                try:
                    self.current_process.terminate()
                except Exception:
                    pass

        try:
            self.log("Iniciando o GAM (gam.py)...", "INFO")
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

            subprocess.Popen(
                [sys.executable, str(self.path_gam)],
                cwd=str(self.path_gam.parent),
                creationflags=creationflags,
                close_fds=True
            )
            self.log("[SUCESSO] GAM iniciado com sucesso! Encerrando Painel de Apoio...", "SUCCESS")
            # Encerra a janela gráfica atual
            self.root.destroy()
        except Exception as e:
            err = f"Falha ao iniciar o GAM: {e}"
            messagebox.showerror("Erro ao Abrir GAM", err)
            self.log(f"[ERRO] {err}", "ERROR")

    def abrir_planilhas_pos_min_max(self):
        """
        Ao finalizar a execução do 1-min_max.py:
        1. Abre a planilha de digitar (digitar.xlsx / digitar.csv no GAM/bd_saida)
        2. Abre a planilha de resultado de ajuste (ajustepp.xlsx)
        """
        self.log("Finalização do cálculo detectada. Abrindo planilhas do processo...", "INFO")

        # 1. Abrir a Planilha de Digitar (GAM/bd_saida/digitar.xlsx)
        candidatos_digitar = [
            self.path_digitar,
            self.path_digitar_csv,
            self.aplicativos_dir / "bd_saida" / "digitar.xlsx",
        ]
        abriu_digitar = False
        for p_dig in candidatos_digitar:
            if p_dig.exists():
                try:
                    self.log(f"Abrindo automaticamente a planilha de digitar: {p_dig.name}...", "INFO")
                    os.startfile(str(p_dig))
                    self.log(f"[SUCESSO] Planilha de digitar '{p_dig.name}' aberta com sucesso no Excel!", "SUCCESS")
                    abriu_digitar = True
                    break
                except Exception as e:
                    self.log(f"[ERRO] Falha ao abrir planilha de digitar '{p_dig.name}': {e}", "ERROR")

        if not abriu_digitar:
            self.log("[AVISO] Planilha 'digitar.xlsx' não localizada em 'GAM/bd_saida'.", "WARNING")

        # Pequeno intervalo para o Windows/Excel estabilizar antes de abrir o segundo arquivo
        time.sleep(0.5)

        # 2. Abrir o resultado de ajustepp.xlsx
        self.abrir_resultado_ajustepp()

    def abrir_resultado_ajustepp(self):
        """Localiza e abre o arquivo de resultado gerado pelo 1-min_max.py."""
        self.log("Localizando o resultado 'ajustepp.xlsx'...", "INFO")

        # Candidatos onde o 1-min_max.py pode ter salvo ou movido o arquivo
        candidatos = [
            self.path_ajustepp_gam,
            self.path_ajustepp_minmax,
        ]

        # Verifica também se foi gerado algum resultado_YYYYMMDD_HHMMSS.xlsx
        pasta_minmax = self.path_min_max.parent
        if pasta_minmax.exists():
            for f in pasta_minmax.glob("resultado_*.xlsx"):
                candidatos.append(f)

        # Filtra os existentes e ordena pelo mais recente
        existentes = [p for p in candidatos if p.exists()]
        if not existentes:
            self.log("[AVISO] Não foi possível localizar o arquivo 'ajustepp.xlsx' após a execução.", "WARNING")
            messagebox.showwarning(
                "Resultado Não Encontrado",
                "O script foi executado, mas 'ajustepp.xlsx' não foi encontrado nas pastas esperadas:\n"
                f"- {self.path_ajustepp_gam}\n"
                f"- {self.path_ajustepp_minmax}"
            )
            return

        existentes.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        arquivo_alvo = existentes[0]

        try:
            self.log(f"Abrindo automaticamente o resultado: {arquivo_alvo}...", "INFO")
            os.startfile(str(arquivo_alvo))
            self.log(f"[SUCESSO] Arquivo '{arquivo_alvo.name}' aberto automaticamente no Excel!", "SUCCESS")
        except Exception as e:
            msg_err = f"Erro ao abrir automaticamente '{arquivo_alvo.name}': {e}"
            self.log(f"[ERRO] {msg_err}", "ERROR")
            messagebox.showerror("Erro ao Abrir Arquivo", msg_err)

    # =========================================================================
    # MOTOR DE EXECUÇÃO EM SEGUNDO PLANO
    # =========================================================================
    def iniciar_subprocesso(self, script_path: Path, titulo: str, ao_finalizar_callback=None, stdin_data: str = None):
        """Executa um script Python em thread separada com streaming de logs e suporte a entrada automática."""
        self.is_running = True
        self.stop_requested = False
        self.lbl_status.config(text=f"Status: Executando {titulo}...", fg="#0052cc")
        self.atualizar_estado_botoes()

        self.log(f"============================================================", "INFO")
        self.log(f"INICIANDO EXECUÇÃO: {titulo}", "INFO")
        self.log(f"Caminho: {script_path}", "INFO")
        self.log(f"============================================================", "INFO")

        thread = threading.Thread(
            target=self._worker_execucao,
            args=(script_path, titulo, ao_finalizar_callback, stdin_data),
            daemon=True
        )
        thread.start()

    def _worker_execucao(self, script_path: Path, titulo: str, ao_finalizar_callback, stdin_data: str = None):
        """Worker em thread que alimenta a fila de mensagens e gerencia a comunicação bidirecional com o processo."""
        cwd_dir = script_path.parent
        env = os.environ.copy()
        # Força stdout não bufferizado para os prints saírem em tempo real
        env["PYTHONUNBUFFERED"] = "1"

        cmd = [sys.executable, "-u", str(script_path)]
        start_time = time.time()

        try:
            # CREATE_NO_WINDOW para evitar janelas pretas indesejadas de console
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            self.current_process = subprocess.Popen(
                cmd,
                cwd=str(cwd_dir),
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                creationflags=creationflags
            )

            # Se houver respostas pré-configuradas pela tela gráfica, injeta no stdin do processo
            if stdin_data and self.current_process.stdin:
                try:
                    self.current_process.stdin.write(stdin_data.encode("utf-8"))
                    self.current_process.stdin.flush()
                except Exception as e:
                    self.queue.put({"tipo": "log", "msg": f"[AVISO] Falha ao enviar respostas prévias ao stdin: {e}"})

            # Leitura linha a linha em tempo real
            # Usando decodificação flexível para caracteres acentuados no Windows
            while True:
                line_bytes = self.current_process.stdout.readline()
                if not line_bytes:
                    break
                try:
                    line = line_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        line = line_bytes.decode("latin1")
                    except Exception:
                        line = line_bytes.decode("utf-8", errors="replace")

                line = line.rstrip("\r\n")
                if line.strip():
                    self.queue.put({"tipo": "log", "msg": line})

            self.current_process.wait()
            rc = self.current_process.returncode
            duracao = time.time() - start_time

            self.queue.put({
                "tipo": "fim",
                "titulo": titulo,
                "returncode": rc,
                "duracao": duracao,
                "callback": ao_finalizar_callback,
                "interrompido": self.stop_requested
            })

        except Exception as e:
            self.queue.put({
                "tipo": "erro_fatal",
                "titulo": titulo,
                "erro": str(e)
            })
        finally:
            self.current_process = None

    def parar_execucao_atual(self):
        """Interrompe o processo ativo se o usuário clicar no botão PARAR."""
        if not self.is_running or not self.current_process:
            return

        if messagebox.askyesno("Confirmar Parada", "Deseja realmente interromper o processo em execução?"):
            self.stop_requested = True
            self.log(">>> Solicitação de parada forçada enviada ao processo...", "WARNING")
            try:
                self.current_process.terminate()
                time.sleep(0.5)
                if self.current_process and self.current_process.poll() is None:
                    self.current_process.kill()
            except Exception as e:
                self.log(f"Erro ao encerrar processo: {e}", "ERROR")

    def processar_fila(self):
        """Consome eventos enviados pelo worker thread na thread principal da GUI."""
        try:
            while True:
                item = self.queue.get_nowait()
                tipo = item.get("tipo")

                if tipo == "log":
                    self.log(item["msg"])

                elif tipo == "fim":
                    self.is_running = False
                    rc = item.get("returncode")
                    duracao = item.get("duracao", 0)
                    titulo = item.get("titulo")
                    interrompido = item.get("interrompido")
                    cb = item.get("callback")

                    if interrompido:
                        self.log(f"\n[AVISO] {titulo} foi interrompido pelo usuário após {duracao:.1f}s.", "WARNING")
                        self.lbl_status.config(text=f"Status: {titulo} interrompido.", fg="#c0392b")
                    elif rc == 0:
                        self.log(f"\n[SUCESSO] {titulo} concluído com sucesso em {duracao:.1f}s!", "SUCCESS")
                        self.lbl_status.config(text=f"Status: {titulo} finalizado com sucesso.", fg="#27ae60")
                        self.tocar_som_notificacao()
                        # Se houver callback pós-sucesso (ex: abrir ajustepp.xlsx)
                        if cb:
                            try:
                                cb()
                            except Exception as e:
                                self.log(f"Erro ao executar ação pós-conclusão: {e}", "ERROR")
                    else:
                        self.log(f"\n[ERRO] {titulo} finalizou com código de erro {rc} após {duracao:.1f}s.", "ERROR")
                        self.lbl_status.config(text=f"Status: Erro ao executar {titulo} (Código {rc}).", fg="#c0392b")

                    self.atualizar_estado_botoes()

                elif tipo == "erro_fatal":
                    self.is_running = False
                    titulo = item.get("titulo")
                    err = item.get("erro")
                    self.log(f"[ERRO FATAL] Falha interna ao executar {titulo}: {err}", "ERROR")
                    self.lbl_status.config(text=f"Status: Falha ao executar {titulo}.", fg="#c0392b")
                    self.atualizar_estado_botoes()

                self.queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.processar_fila)

    def ao_fechar_janela(self):
        """Verifica se há processos em execução antes de fechar a janela."""
        if self.is_running:
            resp = messagebox.askyesno(
                "Processo em Execução",
                "Existe uma automação rodando no momento. Deseja realmente interromper e fechar?"
            )
            if not resp:
                return
            if self.current_process:
                try:
                    self.current_process.terminate()
                except Exception:
                    pass

        self.root.destroy()


def main():
    root = tk.Tk()
    app = PainelApoioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
