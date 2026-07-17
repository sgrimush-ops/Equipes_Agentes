import os
import sys
import time
import subprocess
import pyautogui
from pynput.mouse import Controller, Button
from typing import Tuple, Optional

# Tenta importar pytesseract e cv2 para modo OCR
try:
    import cv2
    import numpy as np
    from PIL import ImageGrab
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

try:
    from rapidocr_onnxruntime import RapidOCR
    import re
    HAS_RAPIDOCR = True
except ImportError:
    HAS_RAPIDOCR = False


def _auto_discover_tesseract() -> Optional[str]:
    """
    Busca automaticamente pelo executável do Tesseract no Windows,
    incluindo pastas locais do pendrive para funcionamento standalone.
    """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    possiveis_caminhos = [
        os.path.join(base_dir, "tesseract", "tesseract.exe"),
        os.path.join(base_dir, "tesseract.exe"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"D:\Program Files\Tesseract-OCR\tesseract.exe",
        r"E:\Program Files\Tesseract-OCR\tesseract.exe",
    ]

    for c in possiveis_caminhos:
        if os.path.exists(c):
            return c

    # Tenta achar no PATH do sistema via onde/which
    try:
        res = subprocess.run(['where', 'tesseract'], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        caminhos_path = res.stdout.strip().split('\n')
        if caminhos_path and os.path.exists(caminhos_path[0].strip()):
            return caminhos_path[0].strip()
    except Exception:
        pass

    return None


class ScreenReader:
    """
    Módulo responsável pela leitura visual da tela Consinco via OCR de alta precisão.
    Como o grid de Quitação de Título não permite cópia (Ctrl+C), o modo 'ocr' é
    ativado por padrão com técnicas avançadas de processamento de imagem (OpenCV):
    - Upscaling de 2.5x com interpolação bicúbica
    - Inversão automática de cor para linhas selecionadas (fundo preto e texto branco)
    - Binarização de Otsu e salvamento de imagens de depuração.
    """
    def __init__(self, mode: str = "ocr"):
        self.mode = mode
        self.mouse = Controller()
        self.tesseract_path: Optional[str] = None
        self.rapid_ocr = RapidOCR() if HAS_RAPIDOCR else None
        self.configurar_ocr()

        # Garante pasta de debug para inspecionar os recortes capturados
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.debug_dir = os.path.join(base_dir, "debug_ocr")
        os.makedirs(self.debug_dir, exist_ok=True)

    def configurar_ocr(self):
        if HAS_TESSERACT:
            caminho = _auto_discover_tesseract()
            if caminho:
                self.tesseract_path = caminho
                pytesseract.pytesseract.tesseract_cmd = caminho
                print(f"[ScreenReader] Tesseract-OCR configurado com sucesso em: {caminho}")
            else:
                print("[ScreenReader AVISO] executável 'tesseract.exe' não encontrado nos caminhos padrão. Se o OCR falhar, verifique a instalação.")

    def set_mode(self, mode: str):
        self.mode = mode

    def ler_celula_ocr(self, x: int, y: int, largura: int = 160, altura: int = 26, num_only: bool = False, debug_name: str = "snippet") -> str:
        """
        Captura um recorte visual em torno da coordenada (x, y), aplica processamento de imagem
        avançado para maximizar a precisão do Tesseract e retorna o texto extraído.
        """
        if not (HAS_OPENCV and HAS_TESSERACT):
            msg = "[ERRO OCR] Bibliotecas OpenCV/Pytesseract não instaladas neste ambiente Python."
            print(msg)
            return ""

        if HAS_TESSERACT and not self.tesseract_path:
            # Tenta redescobrir caso o usuário tenha copiado a pasta agora
            self.configurar_ocr()

        try:
            # Centraliza o retângulo de recorte (ou ajusta para a direita no caso de números)
            if num_only:
                # Para Valor em Aberto, joga o box um pouco mais para a direita para não pegar a coluna de data (/2026)
                left = int(x - largura * 0.38)
            else:
                left = int(x - largura / 2)
            top = int(y - altura / 2)
            bbox = (left, top, left + largura, top + altura)

            screenshot = ImageGrab.grab(bbox=bbox)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 1. Upscaling 2.5x para melhorar a nitidez de fontes pequenas de tabelas (Delphi/Oracle)
            gray_scaled = cv2.resize(gray, (0, 0), fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)

            # 2. Inversão inteligente de cor:
            # Na linha selecionada do Consinco, o contudo fica branco e a cor de fundo fica preta.
            # O Tesseract lê com 99%+ de precisão quando o texto é PRETO sobre fundo BRANCO.
            mean_val = np.mean(gray_scaled)
            if mean_val < 130:
                # Fundo predominantemente escuro -> inverte
                gray_scaled = cv2.bitwise_not(gray_scaled)

            # 3. Binarização / Thresholding de Otsu
            _, thresh = cv2.threshold(gray_scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 4. Salva a imagem processada para depuração pelo usuário/desenvolvedor
            try:
                cv2.imwrite(os.path.join(self.debug_dir, f"{debug_name}.png"), thresh)
            except Exception:
                pass

            # 5. Executa OCR (Tesseract como primeira opção, RapidOCR como motor nativo sem instalador)
            text = ""
            if HAS_TESSERACT and self.tesseract_path:
                try:
                    config = "--psm 7"
                    if num_only:
                        config += " -c tessedit_char_whitelist=0123456789,-."
                    else:
                        config += " -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz/-"
                    raw_tess = pytesseract.image_to_string(thresh, config=config).strip()
                    if num_only and raw_tess:
                        token = raw_tess.split()[-1] if ' ' in raw_tess else raw_tess
                        token_clean = re.sub(r'^.*?(?:/202[0-9]|202[0-9](?=[0-9]{1,6}[,.][0-9]{2}))', '', token)
                        text = re.sub(r'[^0-9,\-\.]', '', token_clean)
                    else:
                        text = raw_tess
                except Exception as e_tess:
                    print(f"[ScreenReader AVISO] Falha Tesseract: {e_tess}")

            # Se Tesseract não estiver disponível ou retornar vazio, usa RapidOCR nativo (ONNX)
            if not text and self.rapid_ocr:
                try:
                    # RapidOCR aceita imagem BGR ou Gray/Thresh diretamente
                    res, _ = self.rapid_ocr(thresh)
                    if res:
                        raw_list = [str(item[1]).strip() for item in res if item[1]]
                        if num_only and len(raw_list) > 1:
                            # Pega sempre o último bloco da direita (o valor em aberto, ignorando datas)
                            raw = raw_list[-1]
                        else:
                            raw = " ".join(raw_list)

                        if num_only:
                            token = raw.split()[-1] if ' ' in raw else raw
                            token_clean = re.sub(r'^.*?(?:/202[0-9]|202[0-9](?=[0-9]{1,6}[,.][0-9]{2}))', '', token)
                            text = re.sub(r'[^0-9,\-\.]', '', token_clean)
                        else:
                            text = re.sub(r'[^0-9a-zA-Z/\-]', '', raw)
                        text = text.strip()
                except Exception as e_rapid:
                    print(f"[ScreenReader AVISO] Falha RapidOCR: {e_rapid}")

            return text

        except Exception as e:
            print(f"[ScreenReader OCR ERRO] Falha ao processar OCR na posição ({x}, {y}): {e}")
            return ""

    def _get_clipboard_text(self) -> str:
        """Obtém texto do clipboard (modo secundário caso habilitado no futuro)."""
        if HAS_PYPERCLIP:
            try:
                text = pyperclip.paste()
                if text is not None:
                    return str(text).strip()
            except Exception:
                pass

        if sys.platform == "win32":
            try:
                res = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', 'Get-Clipboard'],
                    capture_output=True, text=True, check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return res.stdout.strip()
            except Exception:
                pass
        return ""

    def _clear_clipboard(self):
        if HAS_PYPERCLIP:
            try:
                pyperclip.copy("")
                return
            except Exception:
                pass
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ['powershell', '-NoProfile', '-Command', 'Set-Clipboard -Value $null'],
                    check=False, creationflags=subprocess.CREATE_NO_WINDOW
                )
            except Exception:
                pass

    def ler_celula_clipboard(self, x: int, y: int, delay_copia: float = 0.25) -> str:
        """Modo alternativo via clipboard."""
        try:
            self._clear_clipboard()
            time.sleep(0.05)
            self.mouse.position = (int(x), int(y))
            time.sleep(0.05)
            self.mouse.click(Button.left, 1)
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(delay_copia)
            text = self._get_clipboard_text()
            if not text:
                self.mouse.click(Button.left, 2)
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(delay_copia)
                text = self._get_clipboard_text()
            return text.strip()
        except Exception as e:
            print(f"[ScreenReader] Erro na leitura via clipboard em ({x}, {y}): {e}")
            return ""

    def ler_linha(self, x_titulo: int, x_valor: int, y_linha: int) -> Tuple[str, str]:
        """
        Lê simultaneamente o Título e o Valor em Aberto da linha especificada.
        Como na tela Quitação de Título o Consinco não permite copiar (Ctrl+C),
        o modo OCR realiza o recorte da tela e extrai o texto com alta nitidez.
        """
        if self.mode == "ocr":
            # Captura com whitelists otimizadas e salva snippets em debug_ocr/
            t_lido = self.ler_celula_ocr(x_titulo, y_linha, largura=150, altura=24, num_only=False, debug_name="ultimo_titulo")
            v_lido = self.ler_celula_ocr(x_valor, y_linha, largura=85, altura=24, num_only=True, debug_name="ultimo_valor")
            return t_lido, v_lido
        else:
            t_lido = self.ler_celula_clipboard(x_titulo, y_linha)
            v_lido = self.ler_celula_clipboard(x_valor, y_linha)
            return t_lido, v_lido
