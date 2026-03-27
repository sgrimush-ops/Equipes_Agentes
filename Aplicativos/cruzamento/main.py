import customtkinter as ctk
import pandas as pd
import os
import threading
from tkinter import ttk
import processamento

# Set appearance mode and default color theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Sistema de Cruzamento e Consulta")
        self.geometry("1100x700")

        # Configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Cruzamento DB", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.sidebar_button_consulta = ctk.CTkButton(self.sidebar_frame, text="Consulta Código", command=self.sidebar_button_event_consulta)
        self.sidebar_button_consulta.grid(row=1, column=0, padx=20, pady=10)
        
        self.sidebar_button_processo = ctk.CTkButton(self.sidebar_frame, text="Processamento", command=self.sidebar_button_event_processo)
        self.sidebar_button_processo.grid(row=2, column=0, padx=20, pady=10)
        
        self.sidebar_button_consulta_gerencial = ctk.CTkButton(self.sidebar_frame, text="Consulta Gerencial", command=self.sidebar_button_event_consulta_gerencial)
        self.sidebar_button_consulta_gerencial.grid(row=3, column=0, padx=20, pady=10)

        # Create Frames
        self.consulta_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.processo_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.consulta_gerencial_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # Setup Frames
        self.setup_consulta_frame()
        self.setup_processo_frame()
        self.setup_consulta_gerencial_frame()
        
        # Select default frame
        self.select_frame_by_name("consulta")

    def select_frame_by_name(self, name):
        # set button color for selected button
        self.sidebar_button_consulta.configure(fg_color=("gray75", "gray25") if name == "consulta" else "transparent")
        self.sidebar_button_processo.configure(fg_color=("gray75", "gray25") if name == "processo" else "transparent")
        self.sidebar_button_consulta_gerencial.configure(fg_color=("gray75", "gray25") if name == "consulta_gerencial" else "transparent")

        # show selected frame
        if name == "consulta":
            self.consulta_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.consulta_frame.grid_forget()
            
        if name == "processo":
            self.processo_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.processo_frame.grid_forget()
            
        if name == "consulta_gerencial":
            self.consulta_gerencial_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.consulta_gerencial_frame.grid_forget()

    def sidebar_button_event_consulta(self):
        self.select_frame_by_name("consulta")
        
    def sidebar_button_event_processo(self):
        self.select_frame_by_name("processo")
        
    def sidebar_button_event_consulta_gerencial(self):
        self.select_frame_by_name("consulta_gerencial")

    # --- CONSULTA FRAME LOGIC ---
    def setup_consulta_frame(self):
        self.consulta_frame.grid_columnconfigure(0, weight=1)
        self.consulta_frame.grid_rowconfigure(2, weight=1)

        # Labels and Entries
        self.entry_label = ctk.CTkLabel(self.consulta_frame, text="Digite o Código Interno (CODIGOINT):", font=ctk.CTkFont(size=14))
        self.entry_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")

        self.input_frame = ctk.CTkFrame(self.consulta_frame, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.code_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Ex: 1010407")
        self.code_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.code_entry.bind("<Return>", self.search_code)

        self.search_button = ctk.CTkButton(self.input_frame, text="Consultar", command=self.search_code)
        self.search_button.pack(side="right")

        # Status Label
        self.consulta_status_label = ctk.CTkLabel(self.consulta_frame, text="", text_color="gray")
        self.consulta_status_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")

        # Treeview Area
        self.tree_frame = ctk.CTkFrame(self.consulta_frame)
        self.tree_frame.grid(row=2, column=0, padx=20, pady=0, sticky="nsew")
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#D3D3D3",
                        foreground="black",
                        rowheight=25,
                        fieldbackground="#D3D3D3")
        style.map('Treeview', background=[('selected', '#347083')])

        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        
        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set, selectmode="extended")
        
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)
        
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Load data for query
        self.load_query_data()

    def load_query_data(self):
        file_path = "bd/banco_dados_sw.parquet"
        if os.path.exists(file_path):
            try:
                self.df_query = pd.read_parquet(file_path)
                if 'CODIGOINT' not in self.df_query.columns:
                     self.consulta_status_label.configure(text="Erro: Coluna 'CODIGOINT' não encontrada.", text_color="red")
                     return
                # Remove leading zeros by converting to int then str
                self.df_query['CODIGOINT'] = pd.to_numeric(self.df_query['CODIGOINT'], errors='coerce').fillna(0).astype(int).astype(str)
                self.setup_treeview_columns()
                self.consulta_status_label.configure(text="Banco de dados carregado com sucesso.", text_color="green")
            except Exception as e:
                self.consulta_status_label.configure(text=f"Erro ao ler arquivo: {e}", text_color="red")
        else:
            self.consulta_status_label.configure(text="Arquivo BD não encontrado.", text_color="red")

    def setup_treeview_columns(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(self.df_query.columns)
        self.tree["show"] = "headings"
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="w")

    def search_code(self, event=None):
        search_term = self.code_entry.get().strip()
        if not hasattr(self, 'df_query'):
            self.consulta_status_label.configure(text="Erro: DB não carregado.", text_color="red")
            return
        if not search_term:
            self.consulta_status_label.configure(text="Digite um código.", text_color="orange")
            return
            
        self.tree.delete(*self.tree.get_children())
        
        # Normalize search term (remove leading zeros if numeric)
        if search_term.isdigit():
             search_term = str(int(search_term))
             
        results = self.df_query[self.df_query['CODIGOINT'] == search_term]
        
        if not results.empty:
            self.consulta_status_label.configure(text=f"{len(results)} registros encontrados.", text_color="green")
            for index, row in results.iterrows():
                values = [str(val) for val in row.tolist()]
                self.tree.insert("", "end", values=values)
        else:
            self.consulta_status_label.configure(text="Código não encontrado.", text_color="orange")



    # --- CONSULTA GERENCIAL FRAME LOGIC ---
    def setup_consulta_gerencial_frame(self):
        self.consulta_gerencial_frame.grid_columnconfigure(0, weight=1)
        self.consulta_gerencial_frame.grid_rowconfigure(2, weight=1)

        # Labels and Entries
        self.entry_label_gerencial = ctk.CTkLabel(self.consulta_gerencial_frame, text="Digite o Código do Produto:", font=ctk.CTkFont(size=14))
        self.entry_label_gerencial.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")

        self.input_frame_gerencial = ctk.CTkFrame(self.consulta_gerencial_frame, fg_color="transparent")
        self.input_frame_gerencial.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.code_entry_gerencial = ctk.CTkEntry(self.input_frame_gerencial, placeholder_text="Ex: 1010407")
        self.code_entry_gerencial.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.code_entry_gerencial.bind("<Return>", self.search_code_gerencial)

        self.search_button_gerencial = ctk.CTkButton(self.input_frame_gerencial, text="Consultar", command=self.search_code_gerencial)
        self.search_button_gerencial.pack(side="right")
        
        # Reload Button
        self.reload_button_gerencial = ctk.CTkButton(self.input_frame_gerencial, text="Recarregar Dados", command=self.load_query_data_gerencial, width=120)
        self.reload_button_gerencial.pack(side="right", padx=(0, 10))

        # Status Label
        self.status_label_gerencial = ctk.CTkLabel(self.consulta_gerencial_frame, text="", text_color="gray")
        self.status_label_gerencial.grid(row=3, column=0, padx=20, pady=10, sticky="w")

        # Treeview Area
        self.tree_frame_gerencial = ctk.CTkFrame(self.consulta_gerencial_frame)
        self.tree_frame_gerencial.grid(row=2, column=0, padx=20, pady=0, sticky="nsew")
        
        # Scrollbars
        self.tree_scroll_y_gerencial = ttk.Scrollbar(self.tree_frame_gerencial, orient="vertical")
        self.tree_scroll_x_gerencial = ttk.Scrollbar(self.tree_frame_gerencial, orient="horizontal")
        
        self.tree_gerencial = ttk.Treeview(self.tree_frame_gerencial, yscrollcommand=self.tree_scroll_y_gerencial.set, xscrollcommand=self.tree_scroll_x_gerencial.set, selectmode="extended")
        
        self.tree_scroll_y_gerencial.config(command=self.tree_gerencial.yview)
        self.tree_scroll_x_gerencial.config(command=self.tree_gerencial.xview)
        
        self.tree_scroll_y_gerencial.pack(side="right", fill="y")
        self.tree_scroll_x_gerencial.pack(side="bottom", fill="x")
        self.tree_gerencial.pack(fill="both", expand=True)

        # Load data
        self.load_query_data_gerencial()

    def load_query_data_gerencial(self):
        file_path = os.path.join("bd", "gerencial_atualizado.parquet")
        if os.path.exists(file_path):
            try:
                self.df_query_gerencial = pd.read_parquet(file_path)
                # Ensure Código Produto is string and stripped
                if 'Código Produto' in self.df_query_gerencial.columns:
                     self.df_query_gerencial['Código Produto'] = self.df_query_gerencial['Código Produto'].astype(str).str.strip()
                
                self.setup_treeview_columns_gerencial()
                self.status_label_gerencial.configure(text="Dados gerenciais carregados com sucesso.", text_color="green")
            except Exception as e:
                self.status_label_gerencial.configure(text=f"Erro ao ler arquivo: {e}", text_color="red")
        else:
            self.status_label_gerencial.configure(text="Arquivo 'gerencial_atualizado.parquet' não encontrado. Execute o processamento primeiro.", text_color="orange")

    def setup_treeview_columns_gerencial(self):
        self.tree_gerencial.delete(*self.tree_gerencial.get_children())
        self.tree_gerencial["columns"] = list(self.df_query_gerencial.columns)
        self.tree_gerencial["show"] = "headings"
        for col in self.tree_gerencial["columns"]:
            self.tree_gerencial.heading(col, text=col)
            self.tree_gerencial.column(col, width=100, anchor="w")

    def search_code_gerencial(self, event=None):
        search_term = self.code_entry_gerencial.get().strip()
        if not hasattr(self, 'df_query_gerencial'):
             self.status_label_gerencial.configure(text="Erro: Dados não carregados.", text_color="red")
             return
        if not search_term:
            self.status_label_gerencial.configure(text="Digite um código.", text_color="orange")
            return
            
        self.tree_gerencial.delete(*self.tree_gerencial.get_children())
        
        # Search in 'Código Produto' and 'seqloja'
        # Adjust column name if needed from previous steps inspection
        # Previous inspection of gerencial.xlsx showed 'Código Produto'.
        mask = self.df_query_gerencial['Código Produto'] == search_term
        if 'seqloja' in self.df_query_gerencial.columns:
             mask = mask | (self.df_query_gerencial['seqloja'].astype(str).str.strip() == search_term)

        results = self.df_query_gerencial[mask]
        
        if not results.empty:
            self.status_label_gerencial.configure(text=f"{len(results)} registros encontrados.", text_color="green")
            for index, row in results.iterrows():
                values = [str(val) for val in row.tolist()]
                self.tree_gerencial.insert("", "end", values=values)
        else:
            self.status_label_gerencial.configure(text="Código não encontrado.", text_color="orange")

    # --- PROCESSAMENTO FRAME LOGIC ---
    def setup_processo_frame(self):
        self.processo_frame.grid_columnconfigure(0, weight=1)
        
        self.proc_title = ctk.CTkLabel(self.processo_frame, text="Processamento e Cruzamento", font=ctk.CTkFont(size=20, weight="bold"))
        self.proc_title.grid(row=0, column=0, padx=20, pady=40)
        
        self.proc_desc = ctk.CTkLabel(self.processo_frame, text="Este processo irá:\n1. Criar chave 'seqloja' no gerencial.xlsx\n2. Cruzar informações com os arquivos Parquet\n3. Gerar 'gerencial_atualizado.xlsx' com as novas colunas.", font=ctk.CTkFont(size=14))
        self.proc_desc.grid(row=1, column=0, padx=20, pady=20)
        
        self.btn_processar = ctk.CTkButton(self.processo_frame, text="Atualizar Gerencial", command=self.run_processamento, height=50, font=ctk.CTkFont(size=16))
        self.btn_processar.grid(row=2, column=0, padx=20, pady=40)
        
        self.proc_status_label = ctk.CTkLabel(self.processo_frame, text="", font=ctk.CTkFont(size=14))
        self.proc_status_label.grid(row=3, column=0, padx=20, pady=20)
        
        self.btn_open_excel = ctk.CTkButton(self.processo_frame, text="Abrir Excel Atualizado", command=self.open_excel_file, fg_color="green", hover_color="darkgreen")
        self.btn_open_excel.grid(row=4, column=0, padx=20, pady=20)
        
    def open_excel_file(self):
        file_path = "gerencial_atualizado.xlsx"
        if os.path.exists(file_path):
            os.startfile(file_path)
            self.proc_status_label.configure(text="Arquivo aberto.", text_color="blue")
        else:
            self.proc_status_label.configure(text="Arquivo não encontrado. Processe primeiro.", text_color="red")
        
    def run_processamento(self):
        self.proc_status_label.configure(text="Processando... Aguarde.", text_color="blue")
        self.btn_processar.configure(state="disabled")
        
        # Run in a separate thread to not freeze UI
        thread = threading.Thread(target=self.execute_update_logic)
        thread.start()
        
    def execute_update_logic(self):
        success, msg = processamento.atualizar_gerencial()
        
        # Update UI in main thread (using after is safer)
        if success:
            self.after(0, lambda: self.proc_status_label.configure(text=msg, text_color="green"))
        else:
            self.after(0, lambda: self.proc_status_label.configure(text=msg, text_color="red"))
            
        self.after(0, lambda: self.btn_processar.configure(state="normal"))

if __name__ == "__main__":
    app = App()
    app.mainloop()
