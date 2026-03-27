import time
import ctypes
from actions.base_action import BaseAction

class AcaoSuspenderPC(BaseAction):
    @property
    def name(self) -> str:
        return "Suspender PC"
        
    @property
    def description(self) -> str:
        return "Coloca o computador em modo de suspensão."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if update_callback:
            update_callback({'status': 'Suspendendo...', 'log': 'Suspendendo o PC em 3s...'})
        
        time.sleep(3)
        if stop_event and stop_event.is_set(): return
        
        # Suspensão nativa do Windows (powrprof.dll)
        # 0 = Standby/Sleep, 1 = Force mode, 0 = Disable wake event
        ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
        
        if update_callback:
            update_callback({'status': 'Concluído', 'finished': True, 'log': 'PC Suspenso.'})

    def has_calibration(self) -> bool:
        return False
        
    def calibrate(self, parent_window):
        pass

def get_action():
    return AcaoSuspenderPC()
