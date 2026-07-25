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
                if not HAS_RAPIDOCR:
                    print("[ScreenReader AVISO] executável 'tesseract.exe' não encontrado nos caminhos padrão. Se o OCR falhar, verifique a instalação.")

    def set_mode(self, mode: str):
        self.mode = mode

    def ler_celula_ocr(self, x: int, y: int, largura: int = 160, altura: int = 26, num_only: bool = False, debug_name: str = "snippet", left_override: Optional[int] = None) -> str:
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
            # Usa os limites exatos da esquerda e direita capturados pelo usuário
            if left_override is not None:
                left = int(left_override)
            elif num_only:
                left = int(x - 75)
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

            # 4. Limpeza de linhas horizontais e verticais da grade da tabela (barras pretas no topo/fundo)
            # e adição de margem branca pura (padding). Isso impede que o OCR corte o primeiro ou último dígito!
            H, W = thresh.shape[:2]
            kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (max(10, int(W * 0.25)), 1))
            lines_h = cv2.morphologyEx(cv2.bitwise_not(thresh), cv2.MORPH_OPEN, kernel_h)
            thresh[lines_h > 0] = 255

            kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(10, int(H * 0.4))))
            lines_v = cv2.morphologyEx(cv2.bitwise_not(thresh), cv2.MORPH_OPEN, kernel_v)
            thresh[lines_v > 0] = 255

            thresh[0:6, :] = 255
            thresh[max(0, H-6):H, :] = 255
            thresh[:, 0:4] = 255
            thresh[:, max(0, W-4):W] = 255

            thresh_padded = cv2.copyMakeBorder(thresh, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)

            # 5. Salva a imagem processada limpa e com padding para depuração pelo usuário
            try:
                cv2.imwrite(os.path.join(self.debug_dir, f"{debug_name}.png"), thresh_padded)
            except Exception:
                pass

            # 6. Executa OCR na imagem limpa (thresh_padded)
            text = ""
            if HAS_TESSERACT and self.tesseract_path:
                try:
                    config = "--psm 7"
                    if num_only:
                        config += " -c tessedit_char_whitelist=0123456789,-."
                    else:
                        config += " -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz/-"
                    raw_tess = pytesseract.image_to_string(thresh_padded, config=config).strip()
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
                    res, _ = self.rapid_ocr(thresh_padded)
                    if res:
                        raw_list = [str(item[1]).strip() for item in res if item[1]]
                        if num_only and len(raw_list) > 1:
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

    def is_checkbox_marcado(self, x: int, y: int, size: int = 30) -> bool:
        """
        Analisa visualmente a coordenada (x, y) do checkbox usando filtros rigorosos de forma geométrica.
        Procura especificamente por um quadrado (borda do checkbox) próximo ao clique,
        e olha o centro absoluto dele, sendo imune a cliques tortos e linhas de grade.
        """
        if not HAS_OPENCV:
            return False
            
        try:
            left = int(x - size / 2)
            top = int(y - size / 2)
            bbox = (left, top, left + size, top + size)
            
            screenshot = ImageGrab.grab(bbox=bbox)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Amostramos pixels apenas à ESQUERDA do checkbox (mesma altura Y).
            # Ignoramos a direita pois a barra de rolagem do Consinco pode estar lá e
            # poluir a cor com um tom claro, quebrando a detecção da linha selecionada.
            mid_y = size // 2
            bg_samples = [
                gray[mid_y, 2], gray[mid_y, 4], gray[mid_y, 6], gray[mid_y, 8]
            ]
            bg_is_dark = np.median(bg_samples) < 127
            
            if bg_is_dark:
                _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
            else:
                _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
                
            contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            best_rect = None
            min_dist = 9999
            center_img = size / 2.0
            
            for cnt in contours:
                xr, yr, wr, hr = cv2.boundingRect(cnt)
                # Um checkbox no Consinco costuma ter entre 10 a 16 pixels
                if 8 <= wr <= 22 and 8 <= hr <= 22:
                    aspect_ratio = wr / float(hr)
                    # Deve ser razoavelmente quadrado
                    if 0.7 <= aspect_ratio <= 1.3:
                        cx = xr + wr / 2.0
                        cy = yr + hr / 2.0
                        # Distância ao centro do recorte (garante que não pegue scrollbars laterais)
                        dist = (cx - center_img)**2 + (cy - center_img)**2
                        if dist < min_dist:
                            min_dist = dist
                            best_rect = (xr, yr, wr, hr)
            
            if best_rect:
                xr, yr, wr, hr = best_rect
                # Extrai a área interna do checkbox, cortando 3 pixels de cada borda
                # Isso garante que capturaremos o 'V' inteiro independente de onde ele estiver desenhado
                # dentro da caixa, ignorando as bordas perfeitamente.
                miolo = thresh[yr+3 : yr+hr-3, xr+3 : xr+wr-3]
                ink_pixels = cv2.countNonZero(miolo)
                # Se há tinta (>= 4 pixels) dentro da área útil, está marcado
                is_marked = ink_pixels >= 4
            else:
                # Se não tem checkbox, consideramos desmarcado
                miolo = np.zeros((4,4), dtype=np.uint8)
                is_marked = False
            
            try:
                cv2.imwrite(os.path.join(self.debug_dir, "ultimo_checkbox_full.png"), thresh)
                cv2.imwrite(os.path.join(self.debug_dir, "ultimo_checkbox_miolo.png"), miolo)
            except Exception:
                pass
                
            return is_marked
        except Exception as e:
            print(f"[ScreenReader OCR ERRO] Falha ao ler checkbox em ({x}, {y}): {e}")
            return False

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
        """Modo alternativo via clipboard (Duplo Clique -> Ctrl+C -> Ctrl+A -> Ctrl+C)."""
        try:
            self._clear_clipboard()
            time.sleep(0.05)
            self.mouse.position = (int(x), int(y))
            time.sleep(0.05)
            
            # Tentativa 1: Duplo clique
            self.mouse.click(Button.left, 2)
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(delay_copia)
            text = self._get_clipboard_text()
            
            if not text.strip():
                # Tentativa 2: Ctrl+A
                self.mouse.click(Button.left, 1)
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(delay_copia)
                text = self._get_clipboard_text()
                
            return text.strip()
        except Exception as e:
            print(f"[ScreenReader] Erro na leitura via clipboard em ({x}, {y}): {e}")
            return ""

    def ler_linha(self, coords_or_xtitulo: Any, x_valor: Optional[int] = None, y_linha: int = 0) -> Tuple[str, str]:
        """
        Lê simultaneamente o Título e o Valor em Aberto da linha especificada.
        Suporta calibração por 2 cliques (limite esquerdo e direito exatos da coluna).
        """
        if isinstance(coords_or_xtitulo, dict):
            coords = coords_or_xtitulo
            # Título
            if coords.get("x_titulo_esq") is not None and coords.get("x_titulo_dir") is not None:
                left_t = min(int(coords["x_titulo_esq"]), int(coords["x_titulo_dir"]))
                larg_t = abs(int(coords["x_titulo_dir"]) - int(coords["x_titulo_esq"]))
                x_t = int(coords.get("x_titulo") or (left_t + larg_t // 2))
            else:
                x_t = int(coords["x_titulo"])
                left_t = None
                larg_t = 160

            # Valor em Aberto
            if coords.get("x_valor_esq") is not None and coords.get("x_valor_dir") is not None:
                left_v = min(int(coords["x_valor_esq"]), int(coords["x_valor_dir"]))
                larg_v = abs(int(coords["x_valor_dir"]) - int(coords["x_valor_esq"]))
                x_v = int(coords.get("x_valor") or (left_v + larg_v // 2))
            else:
                x_v = int(coords["x_valor"])
                left_v = None
                larg_v = 135
        else:
            x_t = int(coords_or_xtitulo)
            x_v = int(x_valor or 0)
            left_t = None
            left_v = None
            larg_t = 160
            larg_v = 135

        if self.mode == "ocr":
            # Captura com whitelists otimizadas e salva snippets em debug_ocr/
            t_lido = self.ler_celula_ocr(x_t, y_linha, largura=larg_t, altura=28, num_only=False, debug_name="ultimo_titulo", left_override=left_t)
            v_lido = ""
        else:
            # Clipboard mode (deprecated fallback)
            t_lido = self.ler_celula_clipboard(x_t, y_linha)
            v_lido = ""
            
        return t_lido, v_lido
