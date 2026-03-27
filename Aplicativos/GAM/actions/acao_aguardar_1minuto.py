import time
from actions.base_action import BaseAction

class AcaoAguardar(BaseAction):
    @property
    def name(self) -> str:
        return "Aguardar 1 Minuto"
        
    @property
    def description(self) -> str:
        return "Pausa a execução da macro por 60 segundos (1 minuto) para aguardar o processamento do sistema."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        total_seconds = 60
        
        if update_callback:
            update_callback({'status': 'Aguardando...', 'log': f'Iniciando pausa de {total_seconds} segundos.'})
            
        for i in range(total_seconds):
            if stop_event and stop_event.is_set():
                if update_callback:
                    update_callback({'log': 'Espera interrompida pelo usuário.'})
                return
                
            while pause_event and pause_event.is_set():
                if stop_event and stop_event.is_set():
                    return
                time.sleep(0.5)
                
            time.sleep(1)
            
            # Atualiza o log a cada 10 segundos para mostrar que está vivo
            if (i + 1) % 10 == 0 and update_callback:
                restante = total_seconds - (i + 1)
                update_callback({'log': f'Aguardando... {restante} segundos restantes.'})

        if update_callback:
            update_callback({'status': 'Concluído', 'finished': True, 'log': 'Pausa de 1 minuto finalizada.'})

    def has_calibration(self) -> bool:
        return False
        
    def calibrate(self, parent_window):
        pass

def get_action():
    return AcaoAguardar()
