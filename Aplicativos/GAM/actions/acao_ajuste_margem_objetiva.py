import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actions.base_action import BaseAction
from core.digitador_margem_objetiva import MargemObjetivaProcessor

class AcaoAjusteMargemObjetiva(BaseAction):
    @property
    def name(self) -> str:
        return "Ajuste de Margem Objetiva"
        
    @property
    def description(self) -> str:
        return "Executa o preenchimento de margem objetiva via interface Consinco."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if update_callback:
            update_callback({'status': 'Preparando execução da Margem Objetiva...'})
            
        processor = MargemObjetivaProcessor()
        processor.run(
            update_callback=update_callback,
            stop_event=stop_event,
            pause_event=pause_event
        )

    def has_calibration(self) -> bool:
        return True
        
    def calibrate(self, parent_window):
        import tkinter as tk
        from tkinter import messagebox
        try:
            from core.calibrador_margem_objetiva import MargemObjetivaCalibrationWindow
            MargemObjetivaCalibrationWindow(parent_window)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a calibração: {e}")

def get_action():
    return AcaoAjusteMargemObjetiva()
