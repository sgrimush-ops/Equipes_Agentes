from abc import ABC, abstractmethod
import threading

class BaseAction(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome curto da ação que aparecerá no menu."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição detalhada da ação."""
        pass
        
    @abstractmethod
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        """
        Executa a ação. Deve ser bloqueante (só retorna quando terminar).
        
        Args:
            update_callback: Função que recebe dicionários (ex: {'status': 'info', 'error': 'msg'})
            stop_event: threading.Event para interromper a execução.
            pause_event: threading.Event para pausar a execução.
        """
        pass
        
    def has_calibration(self) -> bool:
        """Retorna True se esta ação possuir processo de calibração independente."""
        return False
        
    def calibrate(self, parent_window):
        """Inicia a calibração da ação (Ex: abre uma janela do tkinter)."""
        pass

    @staticmethod
    def get_coords_path(filename="coords.json") -> str:
        import os
        import sys
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        coords_dir = os.path.join(base_path, 'coords')
        if not os.path.exists(coords_dir):
            try:
                os.makedirs(coords_dir)
            except Exception:
                pass
                
        return os.path.join(coords_dir, filename)
