import cv2
import numpy as np
import pyautogui
from PIL import Image
import os

class VisionEngine:
    """Motor de visão computacional para detecção de elementos de interface."""
    
    def __init__(self, debug_folder: str = "tmp/vision_debug"):
        self.debug_folder = debug_folder
        os.makedirs(self.debug_folder, exist_ok=True)

    def find_on_screen(self, template_path: str, confidence: float = 0.8, region=None, scales=[1.0, 0.9, 0.8, 1.1, 1.2]):
        """
        Localiza uma imagem (template) na tela com suporte a múltiplas escalas.
        Retorna (x, y, w, h) se encontrado, ou None.
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template não encontrado: {template_path}")
            
        screenshot = pyautogui.screenshot(region=region)
        screen_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(template_path)
        
        melhor_max_val = 0
        melhor_max_loc = None
        melhor_w, melhor_h = 0, 0

        for scale in scales:
            # Redimensiona o template
            w = int(template.shape[1] * scale)
            h = int(template.shape[0] * scale)
            
            # Pula se o template ficar maior que a captura da tela
            if w > screen_np.shape[1] or h > screen_np.shape[0]:
                continue
                
            resized = cv2.resize(template, (w, h), interpolation=cv2.INTER_AREA)
            res = cv2.matchTemplate(screen_np, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)

            if max_val > melhor_max_val:
                melhor_max_val = max_val
                melhor_max_loc = max_loc
                melhor_w, melhor_h = w, h

        if melhor_max_val >= confidence:
            offset_x = region[0] if region else 0
            offset_y = region[1] if region else 0
            return (melhor_max_loc[0] + offset_x, melhor_max_loc[1] + offset_y, melhor_w, melhor_h)
        
        return None

    def check_status(self, region, active_img: str, inactive_img: str):
        """Verifica se uma região está com status Ativo ou Inativo."""
        if self.find_on_screen(active_img, region=region):
            return "Ativo"
        if self.find_on_screen(inactive_img, region=region):
            return "Inativo"
        return "Desconhecido"
