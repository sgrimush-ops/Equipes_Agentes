import pyautogui
import time
import re
import cv2
import numpy as np
from PIL import ImageGrab
import subprocess
import sys

class FamiliaDescriptionCleaner:
    """
    Módulo para detectar e corrigir automaticamente descrições de famílias
    com caracteres especiais que causam erro no Consinco.
    
    Fluxo:
    1. Detecta popup de erro de caracteres especiais
    2. Responde "SIM" automaticamente
    3. Remove caracteres especiais da descrição
    4. Salva com F4 e volta com F10
    5. Salva novamente com F4
    6. Continua para o próximo item com F2
    """
    
    def __init__(self):
        self.special_chars_pattern = r'[/,.\-_~!@#$%&*()+=\[\]{};:<>?|\\`\'"\s]+'
        self.error_detected = False
        
    def detect_error_popup(self, timeout=2.0):
        """
        Detecta se há popup de erro de caracteres especiais na tela.
        Procura por padrões visuais ou OCR.
        
        Args:
            timeout: Tempo máximo para aguardar detecção (segundos)
            
        Returns:
            bool: True se erro detectado, False caso contrário
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Captura a tela
                screenshot = ImageGrab.grab()
                img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # Converte para escala de cinza para detecção de texto
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                
                # Procura por características do popup (border amarelo, ícone de aviso)
                # Detecta amarelo (típico de aviso no Consinco)
                hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
                lower_yellow = np.array([15, 100, 100])
                upper_yellow = np.array([35, 255, 255])
                mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
                
                # Se encontrar área amarela significativa, popup foi detectado
                if cv2.countNonZero(mask_yellow) > 500:
                    self.error_detected = True
                    return True
                    
            except Exception as e:
                print(f"[FamiliaCleanerERROR] Erro ao detectar popup: {e}")
                pass
                
            time.sleep(0.1)
        
        return False
    
    def click_sim_button(self):
        """
        Clica no botão "SIM" do popup de erro.
        Usa Enter como método primário (botão padrão do diálogo).
        """
        try:
            # Enter ativa o botão padrão do diálogo (geralmente SIM/OK)
            pyautogui.press('enter')
            time.sleep(0.5)
            print("[FamiliaCleanerINFO] Pressionado Enter para confirmar popup.")
            return True
        except Exception as e:
            print(f"[FamiliaCleanerWARN] Erro ao confirmar popup: {e}")
            return False
    
    def clean_description(self, description):
        """
        Remove caracteres especiais indesejados da descrição.
        
        Args:
            description: Texto original da descrição
            
        Returns:
            str: Descrição limpa
            
        Exemplo:
            "BANDEJA TRAMONTINA SMALL 91390/108" → "BANDEJA TRAMONTINA SMALL 91390108"
        """
        if not description:
            return ""
        
        # Lista de caracteres a remover
        chars_to_remove = ['/', ',', '.', '-', '_', '~', '!', '@', '#', '$', '%', 
                          '&', '*', '(', ')', '+', '=', '[', ']', '{', '}', 
                          ';', ':', '<', '>', '?', '|', '\\', '`', "'", '"']
        
        cleaned = str(description).strip()
        
        for char in chars_to_remove:
            cleaned = cleaned.replace(char, '')
        
        # Remove múltiplos espaços em branco
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def execute_cleanup_flow(self, description_text):
        """
        Executa o fluxo completo de limpeza no Consinco:
        1. Clica SIM no erro
        2. Abre tela de edição
        3. Seleciona e deleta o texto
        4. Digita descrição limpa
        5. Salva com F4
        6. Volta com F10
        7. Salva novamente com F4
        8. F2 para próximo
        
        Args:
            description_text: Texto original da descrição com caracteres especiais
            
        Returns:
            bool: True se limpeza foi bem-sucedida, False caso contrário
        """
        try:
            print(f"[FamiliaCleanerINFO] Iniciando limpeza: '{description_text}'")
            
            # Passo 1: Clicar SIM
            print("[FamiliaCleanerINFO] Clicando em SIM...")
            if not self.click_sim_button():
                print("[FamiliaCleanerWARN] Falha ao clicar SIM, continuando mesmo assim...")
            
            time.sleep(1.0)
            
            # Passo 2: Tela de edição já deve estar aberta
            # Seleciona todo o texto (Ctrl+A)
            print("[FamiliaCleanerINFO] Selecionando todo o texto...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.3)
            
            # Passo 3: Limpa a descrição
            cleaned_desc = self.clean_description(description_text)
            print(f"[FamiliaCleanerINFO] Descrição limpa: '{cleaned_desc}'")
            
            # Delete o texto selecionado
            pyautogui.press('delete')
            time.sleep(0.2)
            
            # Passo 4: Digita a descrição limpa usando Clipboard (mais confiável)
            self._paste_text(cleaned_desc)
            time.sleep(0.3)
            
            # Passo 5: Salva com F4
            print("[FamiliaCleanerINFO] Salvando com F4...")
            pyautogui.press('f4')
            time.sleep(1.0)
            
            # Passo 6: Volta com F10
            print("[FamiliaCleanerINFO] Voltando com F10...")
            pyautogui.press('f10')
            time.sleep(1.0)
            
            # Passo 7: Salva novamente com F4
            print("[FamiliaCleanerINFO] Salvando novamente com F4...")
            pyautogui.press('f4')
            time.sleep(1.0)
            
            # Passo 8: F2 para próximo (será feito no loop principal)
            print("[FamiliaCleanerINFO] Limpeza concluída com sucesso!")
            
            return True
            
        except Exception as e:
            print(f"[FamiliaCleanerERROR] Erro durante execução de limpeza: {e}")
            return False
    
    def _paste_text(self, text):
        """
        Cola texto usando clipboard (mais confiável que pyautogui.write).
        
        Args:
            text: Texto a colar
        """
        try:
            # Copia para clipboard usando PowerShell (Windows)
            if sys.platform == "win32":
                # PowerShell é mais confiável
                cmd = f'powershell -NoProfile -Command "Set-Clipboard -Value \'{text.replace(chr(39), chr(34))}\'\"'
                subprocess.run(cmd, shell=True, check=True, capture_output=True)
            else:
                # Para Linux/Mac (não testado neste contexto)
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), check=True)
            
            time.sleep(0.1)
            
            # Cola o texto
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            
        except Exception as e:
            print(f"[FamiliaCleanerWARN] Erro ao colar via clipboard: {e}")
            # Fallback: tentar com pyautogui.write
            try:
                pyautogui.write(text, interval=0.02)
            except:
                print(f"[FamiliaCleanerERROR] Falha total em digitar texto!")
    
    def handle_error_flow(self, description_text):
        """
        Aguarda o popup de erro aparecer (se houver) e executa o fluxo de limpeza.
        Chamado quando já se sabe que a descrição tem caracteres especiais.
        
        Args:
            description_text: Descrição original
            
        Returns:
            bool: True se limpeza bem-sucedida, False caso contrário
        """
        print("[FamiliaCleanerINFO] Aguardando popup de caracteres especiais...")
        # Aguarda o popup aparecer na tela antes de tentar fechar
        popup_found = self.detect_error_popup(timeout=3.0)
        if popup_found:
            print("[FamiliaCleanerINFO] Popup detectado! Executando limpeza...")
        else:
            print("[FamiliaCleanerWARN] Popup não detectado visualmente, prosseguindo mesmo assim...")
        # Executa o fluxo de limpeza independentemente da detecção visual
        return self.execute_cleanup_flow(description_text)
    
    def validate_cleaned_description(self, description):
        """
        Valida se a descrição está limpa de caracteres especiais.
        
        Args:
            description: Descrição a validar
            
        Returns:
            bool: True se válida (sem caracteres especiais), False caso contrário
        """
        # Lista de caracteres que NÃO são permitidos
        forbidden = set([
            '/', ',', '.', '-', '_', '~', '!', '@', '#', '$', '%',
            '&', '*', '(', ')', '+', '=', '[', ']', '{', '}',
            ';', ':', '<', '>', '?', '|', '\\', '`', "'", '"'
        ])
        
        for char in str(description):
            if char in forbidden:
                return False
        
        return True
