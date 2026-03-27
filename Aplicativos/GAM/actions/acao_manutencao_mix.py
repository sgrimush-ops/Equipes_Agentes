import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actions.base_action import BaseAction
from core.digitador_mix import MixProcessor

class AcaoManutencaoMix(BaseAction):
    @property
    def name(self) -> str:
        return "Manutenção Mix Ativo"
        
    @property
    def description(self) -> str:
        return "Executa a ativação/inativação de produtos no mix (mix.xlsx)."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if update_callback:
            update_callback({'status': 'Preparando execução da Manutenção de Mix...'})
            
        processor = MixProcessor()
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
            from core.calibrador_mix import MixCalibrationWindow
            MixCalibrationWindow(parent_window)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a calibração de mix: {e}")

def get_action():
    return AcaoManutencaoMix()
