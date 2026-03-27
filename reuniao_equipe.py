import os
import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class ReuniaoEquipeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reunião de Equipe - Gestão de Agentes e Skills")
        self.root.geometry("1100x850")
        
        # Configuração de Cores (Dark Mode Premium)
        self.bg_color = "#1e1e2e"
        self.sidebar_color = "#181825"
        self.text_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.skill_accent_color = "#fab387"
        self.save_button_color = "#a6e3a1"
        
        self.root.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Custom Style for Notebook
        self.style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.sidebar_color, foreground=self.text_color, padding=[10, 5])
        self.style.map("TNotebook.Tab", background=[("selected", self.bg_color)], foreground=[("selected", self.accent_color)])
        
        self.base_dir = os.getcwd()
        self.current_file = None
        self.agents = {} # {display_name: absolute_path}
        self.skills = {} # {display_name: absolute_path}
        
        self.setup_ui()
        self.load_agents()
        self.load_skills()

    def setup_ui(self):
        """Inicializa a interface gráfica com sidebar e editor."""
        self.paned_window = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # --- SIDEBAR ---
        self.sidebar_container = tk.Frame(self.paned_window, bg=self.sidebar_color, width=300)
        self.paned_window.add(self.sidebar_container, weight=1)

        self.sidebar_scroll_frame = tk.Frame(self.sidebar_container, bg=self.sidebar_color)
        self.sidebar_scroll_frame.pack(fill=tk.BOTH, expand=True)

        # SEÇÃO DE AGENTES
        self.agent_section = tk.Frame(self.sidebar_scroll_frame, bg=self.sidebar_color)
        self.agent_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tk.Label(self.agent_section, text="👤 SQUAD DE AGENTES", bg=self.sidebar_color, fg=self.accent_color, font=("Segoe UI", 11, "bold"), pady=10).pack(fill=tk.X)
        self.listbox_agents = tk.Listbox(self.agent_section, bg=self.sidebar_color, fg=self.text_color, selectbackground=self.accent_color, borderwidth=0, highlightthickness=0, font=("Segoe UI", 10), height=10)
        self.listbox_agents.pack(fill=tk.BOTH, expand=True, padx=10)
        self.listbox_agents.bind("<<ListboxSelect>>", self.on_agent_select)

        # SEÇÃO DE SKILLS
        self.skill_section = tk.Frame(self.sidebar_scroll_frame, bg=self.sidebar_color)
        self.skill_section.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.skill_section, text="🛠 SKILLS DO SQUAD", bg=self.sidebar_color, fg=self.skill_accent_color, font=("Segoe UI", 11, "bold"), pady=10).pack(fill=tk.X)
        self.listbox_skills = tk.Listbox(self.skill_section, bg=self.sidebar_color, fg=self.text_color, selectbackground=self.skill_accent_color, borderwidth=0, highlightthickness=0, font=("Segoe UI", 10), height=10)
        self.listbox_skills.pack(fill=tk.BOTH, expand=True, padx=10)
        self.listbox_skills.bind("<<ListboxSelect>>", self.on_skill_select)

        # Botões da Sidebar
        self.sidebar_btns = tk.Frame(self.sidebar_container, bg=self.sidebar_color, pady=10)
        self.sidebar_btns.pack(fill=tk.X)

        self.add_btn = tk.Button(self.sidebar_btns, text="+ NOVO ITEM", bg=self.save_button_color, fg="#11111b", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, command=self.add_item_dialog)
        self.add_btn.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)

        self.del_btn = tk.Button(self.sidebar_btns, text="🗑 EXCLUIR SELECIONADO", bg="#f38ba8", fg="#11111b", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, command=self.delete_selected)
        self.del_btn.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)

        # --- EDITOR AREA ---
        self.editor_frame = tk.Frame(self.paned_window, bg=self.bg_color)
        self.paned_window.add(self.editor_frame, weight=4)

        self.header_frame = tk.Frame(self.editor_frame, bg=self.bg_color, pady=10)
        self.header_frame.pack(fill=tk.X)

        self.label_current = tk.Label(self.header_frame, text="Selecione um item para editar", bg=self.bg_color, fg=self.text_color, font=("Segoe UI", 11, "italic"))
        self.label_current.pack(side=tk.LEFT, padx=15)

        self.save_btn = tk.Button(self.header_frame, text="SALVAR ALTERAÇÕES", bg=self.save_button_color, fg="#11111b", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=15, command=self.save_content)
        self.save_btn.pack(side=tk.RIGHT, padx=15)

        self.notebook = ttk.Notebook(self.editor_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.section_texts = {}

    def load_agents(self):
        self.agents = {}
        self.listbox_agents.delete(0, tk.END)
        for root, dirs, files in os.walk(self.base_dir):
            if any(x in root for x in [".gemini", ".git", ".venv", ".motor", "__pycache__"]): continue
            for file in files:
                if file.endswith(".agent.md"):
                    full_path = os.path.join(root, file)
                    display_name = file.replace(".agent.md", "").replace("_", " ").title()
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'name: "' in content:
                                real_name = content.split('name: "')[1].split('"')[0]
                                display_name = real_name
                    except: pass
                    self.agents[display_name] = full_path
                    self.listbox_agents.insert(tk.END, display_name)

    def load_skills(self):
        self.skills = {}
        self.listbox_skills.delete(0, tk.END)
        skills_path = os.path.join(self.base_dir, ".agents", "skills")
        if not os.path.exists(skills_path): return
        for skill_dir in os.listdir(skills_path):
            dir_path = os.path.join(skills_path, skill_dir)
            if not os.path.isdir(dir_path): continue
            skill_md = os.path.join(dir_path, "SKILL.md")
            if os.path.exists(skill_md):
                display_name = skill_dir.replace("-", " ").title()
                try:
                    with open(skill_md, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'name: ' in content:
                            real_name = content.split('name: ')[1].split('\n')[0].strip().strip('"')
                            display_name = real_name
                except: pass
                self.skills[display_name] = skill_md
                self.listbox_skills.insert(tk.END, display_name)

    def on_agent_select(self, event):
        self.listbox_skills.selection_clear(0, tk.END)
        selection = self.listbox_agents.curselection()
        if not selection: return
        self.load_file_to_editor(self.agents[self.listbox_agents.get(selection[0])])

    def on_skill_select(self, event):
        self.listbox_agents.selection_clear(0, tk.END)
        selection = self.listbox_skills.curselection()
        if not selection: return
        self.load_file_to_editor(self.skills[self.listbox_skills.get(selection[0])])

    def load_file_to_editor(self, file_path):
        self.current_file = file_path
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                sections = self.parse_markdown_sections(content)
                self.create_tabs_for_sections(sections)
                self.label_current.config(text=f"Editando: {os.path.basename(file_path)}", font=("Segoe UI", 11, "bold"))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir arquivo: {e}")

    def parse_markdown_sections(self, content):
        sections = {"Configuração (YAML)": ""}
        yaml_match = re.match(r'^---\n(.*?)\n---\n?', content, re.DOTALL)
        if yaml_match:
            sections["Configuração (YAML)"] = yaml_match.group(1).strip()
            rest = content[yaml_match.end():].strip()
        else:
            rest = content.strip()
        parts = re.split(r'\n(## .*)', "\n" + rest)
        if parts[0].strip():
            sections["Cabeçalho"] = parts[0].strip()
        current_header = None
        for i in range(1, len(parts)):
            if parts[i].startswith("## "):
                current_header = parts[i].replace("## ", "").strip()
            elif current_header:
                sections[current_header] = parts[i].strip()
        return sections

    def create_tabs_for_sections(self, sections):
        for tab in self.notebook.tabs(): self.notebook.forget(tab)
        self.section_texts = {}
        for section_name, content in sections.items():
            frame = tk.Frame(self.notebook, bg=self.bg_color)
            self.notebook.add(frame, text=section_name)
            text_area = scrolledtext.ScrolledText(frame, bg="#11111b", fg=self.text_color, insertbackground="white", font=("Consolas", 11), borderwidth=0, padx=10, pady=10)
            text_area.pack(fill=tk.BOTH, expand=True)
            text_area.insert(tk.INSERT, content)
            self.section_texts[section_name] = text_area

    def save_content(self):
        if not self.current_file: return
        try:
            content = ""
            if "Configuração (YAML)" in self.section_texts:
                content += f"---\n{self.section_texts['Configuração (YAML)'].get(1.0, tk.END).strip()}\n---\n\n"
            if "Cabeçalho" in self.section_texts:
                content += f"{self.section_texts['Cabeçalho'].get(1.0, tk.END).strip()}\n\n"
            for section, widget in self.section_texts.items():
                if section in ["Configuração (YAML)", "Cabeçalho"]: continue
                content += f"## {section}\n\n{widget.get(1.0, tk.END).strip()}\n\n"
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content.strip() + "\n")
            messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def delete_selected(self):
        file_path = None
        agent_sel = self.listbox_agents.curselection()
        skill_sel = self.listbox_skills.curselection()
        if agent_sel: file_path = self.agents[self.listbox_agents.get(agent_sel[0])]
        elif skill_sel: file_path = self.skills[self.listbox_skills.get(skill_sel[0])]
        if not file_path: return
        if messagebox.askyesno("Confirmar", f"Excluir '{os.path.basename(file_path)}'?"):
            try:
                os.remove(file_path)
                self.load_agents()
                self.load_skills()
                for tab in self.notebook.tabs(): self.notebook.forget(tab)
                self.current_file = None
            except Exception as e: messagebox.showerror("Erro", e)

    def add_item_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Criar Novo Item")
        dialog.geometry("600x750")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()

        # Selector
        mode_var = tk.StringVar(value="Agente")
        selector_frame = tk.Frame(dialog, bg=self.sidebar_color, pady=10)
        selector_frame.pack(fill=tk.X)
        tk.Label(selector_frame, text="O que deseja criar?", bg=self.sidebar_color, fg=self.text_color, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=20)
        
        rb_agent = tk.Radiobutton(selector_frame, text="Agente (.agent.md)", variable=mode_var, value="Agente", bg=self.sidebar_color, fg=self.accent_color, selectcolor=self.sidebar_color, font=("Segoe UI", 9), command=lambda: self.update_fields())
        rb_agent.pack(side=tk.LEFT, padx=5)
        
        rb_skill = tk.Radiobutton(selector_frame, text="Skill (SKILL.md)", variable=mode_var, value="Skill", bg=self.sidebar_color, fg=self.skill_accent_color, selectcolor=self.sidebar_color, font=("Segoe UI", 9), command=lambda: self.update_fields())
        rb_skill.pack(side=tk.LEFT, padx=5)

        container = tk.Frame(dialog, bg=self.bg_color, pady=10)
        container.pack(fill=tk.BOTH, expand=True)

        entries = {}
        
        # Templates
        templates = {
            "Agente": {
                "Persona": "Role: ...\nIdentity: ...\nCommunication Style: ...",
                "Principles": "1 - Atividade que tem ...\n2 - Atividade complementar ...\n3 - Atividade ...",
                "Operational Framework": "1. Objetivo: ...\n2. Critérios de Decisão: ...\n3. Processo: ..."
            },
            "Skill": {
                "Type": "hybrid",
                "Categories": "data, retail",
                "Glossário": "### [Termo]\n- Definição: ...\n\n### [Outro Termo]\n- Definição: ...",
                "Regras": "1. [Regra de Ouro]: ...\n2. [Padrão de Formatação]: ...\n3. [Validação]: ..."
            }
        }

        def self_update_fields():
            for widget in container.winfo_children(): widget.destroy()
            entries.clear()
            
            mode = mode_var.get()
            is_agent = mode == "Agente"
            fields = [
                ("Nome", "Ex: Danilo Dados" if is_agent else "Ex: Governanca Dados"),
                ("Descrição", "Função do item" if is_agent else "Objetivo da skill")
            ]
            
            if is_agent:
                fields += [("Persona", ""), ("Principles", ""), ("Operational Framework", "")]
            else:
                fields += [("Type", ""), ("Categories", ""), ("Glossário", ""), ("Regras", "")]

            for label, hint in fields:
                f = tk.Frame(container, bg=self.bg_color, pady=5)
                f.pack(fill=tk.X, padx=20)
                tk.Label(f, text=label, bg=self.bg_color, fg=self.accent_color if is_agent else self.skill_accent_color, font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
                
                template = templates.get(mode, {}).get(label, "")
                
                if label in ["Nome", "Descrição", "Type", "Categories"]:
                    e = tk.Entry(f, bg="#11111b", fg=self.text_color, insertbackground="white", font=("Segoe UI", 10), borderwidth=0)
                    e.pack(fill=tk.X, pady=2)
                    if template: e.insert(0, template)
                    elif hint: # Usa placeholder se não houver template
                         pass # O formulário original não tinha placeholder em texto real, apenas no hint visual externo
                    entries[label] = e
                else:
                    t = scrolledtext.ScrolledText(f, bg="#11111b", fg=self.text_color, insertbackground="white", font=("Segoe UI", 10), borderwidth=0, height=6)
                    t.pack(fill=tk.X, pady=2)
                    if template: t.insert(tk.INSERT, template)
                    entries[label] = t

        self.update_fields = self_update_fields
        self.update_fields()

        def create():
            data = {k: (v.get() if hasattr(v, 'get') and not isinstance(v, scrolledtext.ScrolledText) else v.get(1.0, tk.END).strip()) for k, v in entries.items()}
            if not data["Nome"]: return
            
            slug = data["Nome"].lower().replace(" ", "-")
            is_agent = mode_var.get() == "Agente"
            
            if is_agent:
                dir_path = os.path.join(self.base_dir, "Agentes")
                os.makedirs(dir_path, exist_ok=True)
                target = os.path.join(dir_path, f"{slug}.agent.md")
                content = f'---\nname: "{data["Nome"]}"\ndescription: "{data["Descrição"]}"\n---\n\n# {data["Nome"]}\n\n## Persona\n\n{data["Persona"]}\n\n## Principles\n\n{data["Principles"]}\n\n## Operational Framework\n\n{data["Operational Framework"]}\n'
            else:
                dir_path = os.path.join(self.base_dir, ".agents", "skills", slug)
                os.makedirs(dir_path, exist_ok=True)
                target = os.path.join(dir_path, "SKILL.md")
                content = f'---\nname: {data["Nome"]}\ndescription: {data["Descrição"]}\ntype: {data["Type"]}\ncategories:\n  - {data["Categories"]}\n---\n\n# {data["Nome"]}\n\n{data["Descrição"]}\n\n## Glossário de Negócio\n\n{data["Glossário"]}\n\n## Regras de Ouro\n\n{data["Regras"]}\n'

            try:
                with open(target, 'w', encoding='utf-8') as f: f.write(content)
                messagebox.showinfo("Sucesso", "Criado!")
                dialog.destroy()
                self.load_agents(); self.load_skills()
            except Exception as e: messagebox.showerror("Erro", e)

        tk.Button(dialog, text="CRIAR AGORA", bg=self.save_button_color, fg="#11111b", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, command=create, pady=10).pack(fill=tk.X, padx=20, pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = ReuniaoEquipeApp(root)
    root.mainloop()
