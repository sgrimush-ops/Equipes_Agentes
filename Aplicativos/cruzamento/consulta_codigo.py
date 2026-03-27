import customtkinter as ctk
import pandas as pd
from tkinter import ctk
import os

# Set appearance mode and default color theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Consulta de Produto por Código")
        self.geometry("1100x600")

        # Configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Consulta DB", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.file_label = ctk.CTkLabel(self.sidebar_frame, text="Arquivo Carregado:", anchor="w")
        self.file_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        
        self.file_status = ctk.CTkLabel(self.sidebar_frame, text="Nenhum", text_color="gray")
        self.file_status.grid(row=2, column=0, padx=20, pady=(0, 20))

        # Main content area
        self.entry_label = ctk.CTkLabel(self, text="Digite o Código Interno (CODIGOINT):", font=ctk.CTkFont(size=14))
        self.entry_label.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="w")

        self.code_entry = ctk.CTkEntry(self, placeholder_text="Ex: 1010407")
        self.code_entry.grid(row=1, column=1, padx=(20, 0), pady=(0, 20), sticky="ew")
        self.code_entry.bind("<Return>", self.search_code)

        self.search_button = ctk.CTkButton(self, text="Consultar", command=self.search_code)
        self.search_button.grid(row=1, column=2, padx=20, pady=(0, 20), sticky="ew")

        # Results area (Treeview)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#D3D3D3",
                        foreground="black",
                        rowheight=25,
                        fieldbackground="#D3D3D3")
        style.map('Treeview', background=[('selected', '#347083')])

        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.grid(row=2, column=1, columnspan=2, padx=(20, 20), pady=(0, 20), sticky="nsew")
        
        # Scrollbars for Treeview
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        
        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set, selectmode="extended")
        
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)
        
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.status_label = ctk.CTkLabel(self, text="", text_color="red")
        self.status_label.grid(row=3, column=1, columnspan=2, padx=20, pady=10, sticky="w")

        # Load data on startup
        self.load_data()

    def load_data(self):
        file_path = "bd/banco_dados_sw.parquet"
        if os.path.exists(file_path):
            try:
                # Read Parquet file
                self.df = pd.read_parquet(file_path, engine='pyarrow')
                
                # Check if 'CODIGOINT' column exists
                if 'CODIGOINT' not in self.df.columns:
                     self.status_label.configure(text="Erro: Coluna 'CODIGOINT' não encontrada no arquivo.", text_color="red")
                     return

                # Ensure CODIGOINT is string for searching
                self.df['CODIGOINT'] = self.df['CODIGOINT'].astype(str)

                self.file_status.configure(text="Carregado com sucesso (Parquet)!", text_color="green")
                self.setup_treeview_columns()

            except Exception as e:
                self.status_label.configure(text=f"Erro ao ler arquivo: {e}", text_color="red")
                self.file_status.configure(text="Erro de leitura", text_color="red")
        else:
            # Fallback or error if parquet not found
            self.file_status.configure(text="Arquivo Parquet não encontrado", text_color="red")
            self.status_label.configure(text=f"Arquivo '{file_path}' não encontrado.", text_color="red")

    def setup_treeview_columns(self):
        # Clear existing columns
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(self.df.columns)
        self.tree["show"] = "headings"

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="w")

    def search_code(self, event=None):
        search_term = self.code_entry.get().strip()
        
        if not hasattr(self, 'df'):
            self.status_label.configure(text="Erro: Nenhum banco de dados carregado.", text_color="red")
            return

        if not search_term:
            self.status_label.configure(text="Por favor, digite um código.", text_color="orange")
            return

        # Clear previous results
        self.tree.delete(*self.tree.get_children())

        # Filter logic
        # Assuming exact match for ID is desired. For partial match use .str.contains(search_term, na=False)
        results = self.df[self.df['CODIGOINT'] == search_term]

        if not results.empty:
            self.status_label.configure(text=f"{len(results)} registros encontrados.", text_color="green")
            for index, row in results.iterrows():
                # Clean up values for display (remove quotes if any remain)
                values = [str(val).replace('"', '') for val in row.tolist()]
                self.tree.insert("", "end", values=values)
        else:
            self.status_label.configure(text="Nenhum registro encontrado com esse código.", text_color="orange")

if __name__ == "__main__":
    app = App()
    app.mainloop()
