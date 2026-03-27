import os
import sys

# Adiciona o diretório raiz ao sys.path para podermos importar digitador_pedido_loja.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actions.base_action import BaseAction
from core.digitador_pedido_CD_016 import OrderProcessor

class AcaoDigitarPedidoCD016(BaseAction):
    @property
    def name(self) -> str:
        return "Digitar Pedido CD 016"
        
    @property
    def description(self) -> str:
        return "Executa o robô de digitação de pedidos (selecionando 016 no cabeçalho)."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if update_callback:
            update_callback({'status': 'Preparando digitação...'})
            
        processor = OrderProcessor()
        # O método run da classe OrderProcessor já lida com stop_event e pause_event
        processor.run(
            update_callback=update_callback,
            stop_event=stop_event,
            pause_event=pause_event
        )

    def has_calibration(self) -> bool:
        """Indica que a ação tem calibração (a original do ap.py)."""
        return True
        
    def calibrate(self, parent_window):
        import tkinter as tk
        from tkinter import messagebox
        try:
            from core.ap import CalibrationWindow
            # Abre a janela de calibração antiga
            CalibrationWindow(parent_window)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a janela de calibração: {e}")

# Necessário exportar a classe da ação para instanciar no main.py
def get_action():
    return AcaoDigitarPedidoCD016()
