import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actions.base_action import BaseAction
from core.digitador_abastecimento_familia import AbastecimentoFamiliaProcessor

class AcaoAbastecimentoFamilia(BaseAction):
    @property
    def name(self) -> str:
        return "Abastecimento por Família"
        
    @property
    def description(self) -> str:
        return "Executa a alteração direta da forma de abastecimento por família via interface Consinco."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if update_callback:
            update_callback({'status': 'Preparando execução do Abastecimento por Família...'})
            
        processor = AbastecimentoFamiliaProcessor()
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
            from core.calibrador_abastecimento_familia import AbastecimentoFamiliaCalibrationWindow
            AbastecimentoFamiliaCalibrationWindow(parent_window)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a calibração: {e}")

def get_action():
    return AcaoAbastecimentoFamilia()
