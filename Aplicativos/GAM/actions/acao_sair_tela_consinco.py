import time
import pyautogui
from actions.base_action import BaseAction

class AcaoSairTelaPedido(BaseAction):
    @property
    def name(self) -> str:
        return "Fechar tela Consinco"
        
    @property
    def description(self) -> str:
        return "Sai da tela de pedidos atual pressionando Alt+A e depois 's'."
        
    def execute(self, update_callback=None, stop_event=None, pause_event=None):
        if update_callback:
            update_callback({'status': 'Saindo da tela...', 'log': 'Executando atalho para sair da tela de pedidos...'})
        
        # Pequena pausa antes de começar para garantir que a janela está focada
        time.sleep(1)
        if stop_event and stop_event.is_set(): return
        
        # Pressionar Alt + A
        if update_callback: update_callback({'log': 'Pressionando Alt+A...'})
        pyautogui.hotkey('alt', 'a')
        
        time.sleep(0.5) # Pausa para o menu do sistema reagir
        if stop_event and stop_event.is_set(): return
        
        # Pressionar S
        if update_callback: update_callback({'log': 'Pressionando S...'})
        pyautogui.press('s')
        
        time.sleep(0.5)
        
        if update_callback:
            update_callback({'status': 'Concluído', 'finished': True, 'log': 'Comando de saída executado.'})

    def has_calibration(self) -> bool:
        # Esta ação utiliza apenas teclado, não precisa mapear a tela.
        return False
        
    def calibrate(self, parent_window):
        pass

def get_action():
    return AcaoSairTelaPedido()
