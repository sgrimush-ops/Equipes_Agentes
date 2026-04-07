import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Diretório base dos Aplicativos
BASE_DIR = Path(__file__).parent.resolve()

# Mapeamento dos projetos e seus respectivos entry points (arquivos principais de inicialização)
PROJETOS = {
    "BancoDadosSW": "convert_txt_to_excel.py",
    "ExcluiColuna": "ap.py",
    "GAM (Gerenciador de Macros)": "main.py",
    "Pendencias": "resumo.py", # Baseado nos arquivos locais
    "Consumo (Parquet)": "ap.py",
    "Cruzamento (Core)": "ap.py",
    "Mix de Produtos": "convert_to_parquet.py",
    "Ruptura (ETL CSV)": "rp.py",
    "Ruptura (Dashboard HTML)": "dashboard_comprador.py",
    "Ruptura (Ranking Lojas)": "dashboard_loja.py",
    "Integração Google": "ap.py"
}

# Tradução dos rótulos para o diretório físico
DIR_MAP = {
    "BancoDadosSW": "BancoDadosSW",
    "ExcluiColuna": "lojas_colunas",
    "GAM (Gerenciador de Macros)": "GAM",
    "Pendencias": "pendencias",
    "Consumo (Parquet)": "consumo",
    "Cruzamento (Core)": "cruzamento",
    "Mix de Produtos": "mix",
    "Ruptura (ETL CSV)": "ruptura",
    "Ruptura (Dashboard HTML)": "ruptura",
    "Ruptura (Ranking Lojas)": "ruptura",
    "Integração Google": "integracao_google"
}

def abrir_projeto(nome_botao):
    pasta_projeto = DIR_MAP[nome_botao]
    script_alvo = PROJETOS[nome_botao]
    
    dir_path = BASE_DIR / pasta_projeto
    script_path = dir_path / script_alvo
    
    if not script_path.exists():
        messagebox.showerror("Erro", f"Arquivo de inicialização não encontrado:\n{script_path}")
        return

    # Procura um ambiente virtual (.venv) respeitando as rules.md do projeto
    # O Python do Windows fica em .venv/Scripts/python.exe
    venv_python_local = dir_path / ".venv" / "Scripts" / "python.exe"
    venv_python_root = BASE_DIR.parent / ".venv" / "Scripts" / "python.exe"
    
    if venv_python_local.exists():
        python_exec = str(venv_python_local)
        msg_extra = " (Usando VENV Local do App)"
    elif venv_python_root.exists():
        python_exec = str(venv_python_root)
        msg_extra = " (Usando VENV Principal do Sistema)"
    else:
        python_exec = "python" # Global
        msg_extra = " (Usando Python Global)"
    
    try:
        # Popen lança o processo de forma não-bloqueante; útil para GUIs e processos paralelos
        # Define 'cwd' como o diretório do projeto, assim caminhos relativos lá dentro funcionam!
        subprocess.Popen([python_exec, str(script_path)], cwd=str(dir_path))
        print(f"[{nome_botao}] Iniciado com sucesso!{msg_extra}")
    except Exception as e:
        messagebox.showerror("Erro de Execução", f"Não foi possível iniciar o {nome_botao}.\n\nDetalhes:\n{str(e)}")

class AppMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Menu Central de Aplicativos - Backoffice")
        self.root.geometry("400x550")
        self.root.configure(bg="#2E3440")
        self.root.resizable(False, False)
        
        # Estilos (Design Moderno Dark/Tailwind style)
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TButton",
                        font=("Segoe UI", 11, "bold"),
                        padding=10,
                        background="#4C566A",
                        foreground="#ECEFF4",
                        borderwidth=0)
        style.map("TButton",
                  background=[('active', '#5E81AC')],
                  foreground=[('active', 'white')])

        # Cabecalho
        header_frame = tk.Frame(root, bg="#3B4252", pady=15)
        header_frame.pack(fill=tk.X)
        
        lbl_titulo = tk.Label(header_frame, text="CENTRAL DE AGENTES", font=("Segoe UI", 16, "bold"), bg="#3B4252", fg="#88C0D0")
        lbl_titulo.pack()
        lbl_sub = tk.Label(header_frame, text="Selecione um projeto para iniciar", font=("Segoe UI", 10), bg="#3B4252", fg="#D8DEE9")
        lbl_sub.pack()

        # Botões
        buttons_frame = tk.Frame(root, bg="#2E3440", pady=15, padx=20)
        buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        for nome_display in PROJETOS.keys():
            btn = ttk.Button(buttons_frame, text=nome_display, command=lambda n=nome_display: abrir_projeto(n))
            btn.pack(fill=tk.X, pady=6)

        # Rodapé
        footer = tk.Label(root, text="Ambiente de Automação Inteligente", font=("Segoe UI", 8, "italic"), bg="#2E3440", fg="#4C566A")
        footer.pack(side=tk.BOTTOM, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppMenu(root)
    root.mainloop()
