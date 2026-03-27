if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
import os
import sys
import json
import importlib
import threading
import queue
import time
import pandas as pd
import subprocess

# Adiciona o diretório atual ao sys.path para importações locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports explícitos das ações para o PyInstaller agrupá-las no executável
import actions.acao_aguardar_1minuto
import actions.acao_ajuste_min_max
import actions.acao_aprovar_pedido_manual
import actions.acao_bloquear_tela
import actions.acao_suspender_pc
import actions.acao_digitar_pedido_CD_016

import actions.acao_digitar_pedido_supply
import actions.acao_fechar_tela_ativa
import actions.acao_manutencao_mix
import actions.acao_preparar_manual_supply
import actions.acao_preparar_pedido_loja
import actions.acao_sair_tela_consinco
import actions.acao_whatsapp



class MacroAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Automações e Macros")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        self.actions_available = {}
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.sequences_dir = os.path.join(base_dir, "sequences")
        
        # Garante a criação dos diretórios necessários usando o diretório absoluto real
        for dir_name in [self.sequences_dir, os.path.join(base_dir, "bd_entrada"), os.path.join(base_dir, "bd_saida"), os.path.join(base_dir, "coords")]:
            if not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name)
                except Exception:
                    pass
            
        self.is_running = False
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.queue = queue.Queue()
        
        self.load_action_modules()
        self.create_widgets()
        
        self.root.after(100, self.process_queue)

    def load_action_modules(self):
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        actions_dir = os.path.join(base_dir, "actions")
        if not os.path.exists(actions_dir):
            return
            
        for filename in os.listdir(actions_dir):
            if filename.startswith("acao_") and filename.endswith(".py"):
                module_name = f"actions.{filename[:-3]}"
                try:
                    # Carregamento dinâmico do módulo
                    mod = importlib.import_module(module_name)
                    importlib.reload(mod)
                    if hasattr(mod, 'get_action'):
                        action_instance = mod.get_action()
                        self.actions_available[action_instance.name] = action_instance
                except Exception as e:
                    print(f"Erro ao carregar módulo {filename}: {e}")

    def create_widgets(self):
        # Main Layout: 3 Columns (Left: Actions, Center: Arrows, Right: Sequence)
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- Left Column: Available Actions ---
        left_panel = tk.Frame(main_frame, bg="#f0f0f0")
        left_panel.pack(side="left", fill="both", expand=True)
        tk.Label(left_panel, text="Ações Disponíveis:", font=("Segoe UI", 10, "bold"), bg="#f0f0f0").pack()
        
        self.listbox_avail = tk.Listbox(left_panel, selectmode=tk.SINGLE, font=("Segoe UI", 10))
        self.listbox_avail.pack(fill="both", expand=True, pady=5)
        for name in sorted(self.actions_available.keys()):
            action = self.actions_available[name]
            disp_name = f"{name} *" if action.has_calibration() else name
            self.listbox_avail.insert(tk.END, disp_name)
            
        self.btn_calibrar = tk.Button(left_panel, text="Calibrar Ação Selecionada", command=self.calibrar_acao)
        self.btn_calibrar.pack(fill="x", pady=5)
        
        tk.Label(left_panel, text="* Requer calibração prévia", font=("Segoe UI", 8, "italic"), bg="#f0f0f0", fg="gray").pack(anchor="w")
        
        # --- Center Column: Add/Remove Arrows ---
        center_panel = tk.Frame(main_frame, bg="#f0f0f0")
        center_panel.pack(side="left", padx=10)
        tk.Button(center_panel, text="Adicionar ->", command=self.add_to_sequence, width=12).pack(pady=10)
        tk.Button(center_panel, text="<- Remover", command=self.remove_from_sequence, width=12).pack(pady=10)
        
        # --- Right Column: Macro Sequence ---
        right_panel = tk.Frame(main_frame, bg="#f0f0f0")
        right_panel.pack(side="left", fill="both", expand=True)
        tk.Label(right_panel, text="Sequência (Macro):", font=("Segoe UI", 10, "bold"), bg="#f0f0f0").pack()
        
        self.listbox_seq = tk.Listbox(right_panel, selectmode=tk.SINGLE, font=("Segoe UI", 10))
        self.listbox_seq.pack(fill="both", expand=True, pady=5)
        
        seq_buttons = tk.Frame(right_panel, bg="#f0f0f0")
        seq_buttons.pack(fill="x")
        # Top row: Edit current sequence
        seq_buttons_top = tk.Frame(seq_buttons, bg="#f0f0f0")
        seq_buttons_top.pack(fill="x", pady=2)
        tk.Button(seq_buttons_top, text="Salvar Atual", command=self.save_sequence, width=12).pack(side="left", padx=2)
        tk.Button(seq_buttons_top, text="Limpar", command=self.clear_sequence, width=12).pack(side="left", padx=2)
        
        # Bottom row: Named Sequences
        seq_buttons_bottom = tk.Frame(seq_buttons, bg="#f0f0f0")
        seq_buttons_bottom.pack(fill="x", pady=2)
        tk.Button(seq_buttons_bottom, text="Salvar...", command=self.save_sequence_as, width=10).pack(side="left", padx=2)
        tk.Button(seq_buttons_bottom, text="Carregar...", command=self.load_sequence, width=10).pack(side="left", padx=2)
        tk.Button(seq_buttons_bottom, text="Excluir...", command=self.delete_sequence, width=8).pack(side="left", padx=2)
        
        # --- Bottom Column: Execution & Logs ---
        bottom_frame = tk.Frame(self.root, bg="#f0f0f0", padx=10, pady=10)
        bottom_frame.pack(fill="both", expand=False)
        
        ctrl_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        ctrl_frame.pack(fill="x", pady=5)
        
        self.btn_iniciar = tk.Button(ctrl_frame, text="Iniciar Sequência", command=self.iniciar_sequencia, bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"), width=20)
        self.btn_iniciar.pack(side="left", padx=5)
        
        self.btn_pausar = tk.Button(ctrl_frame, text="PAUSAR", command=self.toggle_pause, state="disabled", bg="#FF9800", fg="white", font=("Segoe UI", 10, "bold"), width=15)
        self.btn_pausar.pack(side="left", padx=5)
        
        self.btn_parar = tk.Button(ctrl_frame, text="PARAR", command=self.parar_sequencia, state="disabled", bg="#FF5252", fg="white", font=("Segoe UI", 10, "bold"), width=15)
        self.btn_parar.pack(side="left", padx=5)
        
        tk.Label(bottom_frame, text="Log de Execução:", font=("Segoe UI", 9, "bold"), bg="#f0f0f0").pack(anchor="w")
        self.log_text = tk.Text(bottom_frame, height=6, font=("Consolas", 9), state="disabled")
        self.log_text.pack(fill="both", expand=True)

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def add_to_sequence(self):
        sel = self.listbox_avail.curselection()
        if sel:
            name = self.listbox_avail.get(sel[0])
            self.listbox_seq.insert(tk.END, name)
            
    def remove_from_sequence(self):
        sel = self.listbox_seq.curselection()
        if sel:
            self.listbox_seq.delete(sel[0])
            
    def clear_sequence(self):
        self.listbox_seq.delete(0, tk.END)
        
    def save_sequence(self):
        # Saves to a default recent sequence file for quick reloading
        seq = list(self.listbox_seq.get(0, tk.END))
        clean_seq = [name[:-2] if name.endswith(" *") else name for name in seq]
        file_path = os.path.join(self.sequences_dir, "ultima_sequencia.json")
        with open(file_path, 'w') as f:
            json.dump(clean_seq, f)
        messagebox.showinfo("Sucesso", "Sequência salva com sucesso como a última executada!")

    def save_sequence_as(self):
        seq = list(self.listbox_seq.get(0, tk.END))
        if not seq:
            messagebox.showwarning("Aviso", "A sequência está vazia. Adicione ações antes de salvar.")
            return

        clean_seq = [name[:-2] if name.endswith(" *") else name for name in seq]
        
        file_path = filedialog.asksaveasfilename(
            initialdir=self.sequences_dir,
            title="Salvar Sequência Como",
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(clean_seq, f)
            messagebox.showinfo("Sucesso", f"Sequência salva em:\n{os.path.basename(file_path)}")

    def load_sequence(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.sequences_dir,
            title="Selecione uma Sequência",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        
        if not file_path:
            return # User canceled
            
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    seq = json.load(f)
                    self.clear_sequence()
                    for name in seq:
                        if name in self.actions_available:
                            action = self.actions_available[name]
                            disp_name = f"{name} *" if action.has_calibration() else name
                            self.listbox_seq.insert(tk.END, disp_name)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar sequência: {e}")
                print(f"Erro ao carregar sequência: {e}")

    def delete_sequence(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.sequences_dir,
            title="Selecione a Sequência para Excluir",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        
        if not file_path:
            return
            
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir '{filename}'?"):
                try:
                    os.remove(file_path)
                    messagebox.showinfo("Sucesso", "Sequência excluída com sucesso!")
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível excluir o arquivo:\n{e}")

    def calibrar_acao(self):
        sel = self.listbox_avail.curselection()
        if sel:
            disp_name = self.listbox_avail.get(sel[0])
            name = disp_name[:-2] if disp_name.endswith(" *") else disp_name
            action = self.actions_available[name]
            if action.has_calibration():
                action.calibrate(self.root)
            else:
                messagebox.showinfo("Aviso", "Esta ação não requer calibração.")
        else:
            messagebox.showwarning("Aviso", "Selecione uma ação na lista à esquerda para calibrar.")


    def update_buttons_state(self):
        if self.is_running:
            self.btn_iniciar.config(state="disabled", bg="#cccccc")
            self.btn_parar.config(state="normal", bg="#FF5252")
            self.btn_pausar.config(state="normal", text="PAUSAR", bg="#FF9800")
            self.btn_calibrar.config(state="disabled")
        else:
            self.btn_iniciar.config(state="normal", bg="#4CAF50")
            self.btn_parar.config(state="disabled", bg="#cccccc")
            self.btn_pausar.config(state="disabled", bg="#cccccc", text="PAUSAR")
            self.btn_calibrar.config(state="normal")

    def toggle_pause(self):
        if not self.is_running: return
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.btn_pausar.config(text="PAUSAR", bg="#FF9800")
            self.log("Retomando execução...")
        else:
            self.pause_event.set()
            self.btn_pausar.config(text="RETOMAR", bg="#2196F3")
            self.log("Pausando execução...")

    def parar_sequencia(self):
        if self.is_running:
            self.log("Solicitando parada da sequência...")
            self.stop_event.set()
            if self.pause_event.is_set():
                self.pause_event.clear()

    def iniciar_sequencia(self):
        seq_display = list(self.listbox_seq.get(0, tk.END))
        if not seq_display:
            messagebox.showwarning("Aviso", "A sequência está vazia.")
            return

        seq = [name[:-2] if name.endswith(" *") else name for name in seq_display]

        self.is_running = True
        self.stop_event.clear()
        self.pause_event.clear()
        self.update_buttons_state()
        
        t = threading.Thread(target=self.run_process_thread, args=(seq,))
        t.daemon = True
        t.start()

    def run_process_thread(self, seq_names):
        try:
            for i, name in enumerate(seq_names):
                if self.stop_event.is_set():
                    self.queue.put({'log': 'Execução interrompida pelo usuário.'})
                    break
                    
                action = self.actions_available.get(name)
                if not action:
                    self.queue.put({'log': f"Erro: Ação '{name}' não encontrada!"})
                    continue
                
                self.queue.put({'log': f"=== Iniciando Ação [{i+1}/{len(seq_names)}]: {name} ==="})
                
                # Executa bloqueando até terminar
                action.execute(
                    update_callback=self.queue.put,
                    stop_event=self.stop_event,
                    pause_event=self.pause_event
                )
                
                if self.stop_event.is_set(): break
                time.sleep(1) # Intervalo pequeno entre ações
                
            self.queue.put({'log': "=== Todas as ações foram concluídas. ===", 'finished_sequence': True})
        except Exception as e:
            self.queue.put({'log': f"Erro Fatal na Thread: {str(e)}", 'finished_sequence': True})

    def process_queue(self):
        try:
            while True:
                data = self.queue.get_nowait()
                if 'log' in data:
                    self.log(data['log'])
                if 'error' in data:
                    self.log(f"ERRO: {data['error']}")
                if 'status' in data:
                    self.log(f"Status: {data['status']}")
                
                if data.get('finished_sequence'):
                    self.is_running = False
                    self.update_buttons_state()
                    self.log("Sequência finalizada.")
                    import winsound
                    # Tocar um som mais discreto (Windows Unlock ou som padrão)
                    try:
                        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                    except Exception:
                        pass # Falha silenciosa caso o som não exista no sistema
                    
                self.queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = MacroAutomationApp(root)
    root.mainloop()
