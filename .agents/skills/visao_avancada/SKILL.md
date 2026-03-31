---
name: Visão Avançada (OpenCV)
description: Detecção robusta de elementos de interface (botões, status, pop-ups) usando reconhecimento de padrões e processamento de imagem.
---

# Visão Avançada para Squad Varejo

Esta skill provê uma camada de inteligência visual para os robôs que interagem com o ERP Consinco, superando limitações de seletores de UI tradicionais.

## Funcionalidades
1. **MatchTemplate Dinâmico**: Localiza imagens de referência com limiar de confiança ajustável.
2. **Multi-Scale Detection**: Encontra elementos mesmo se a janela estiver redimensionada ou com DPI diferente.
3. **Screenshot de Região**: Captura apenas partes específicas da tela (ex: coluna de Status) para economizar processamento.

## Como Usar
Importe o `vision_engine.py` para dentro de qualquer ação:
```python
from skills.visao_avancada.vision_engine import VisionEngine
engine = VisionEngine()
pos = engine.find_on_screen('assets/status_ativo.png', confidence=0.8)
if pos:
    print(f"Elemento encontrado em {pos}")
```

## ⚠️ Avisos Críticos de Ambiente Windows

### DPI e Multi-Monitor: pynput Obrigatório para Cliques Calibrados

A `VisionEngine` retorna coordenadas reais de pixel. Para clicar nessas coordenadas em ambientes Windows com DPI escalado ou múltiplos monitores, **NUNCA use `pyautogui.click()`**. Use `pynput.mouse.Controller`:

```python
# ❌ ERRADO em DPI escalado ou multi-monitor
import pyautogui
pyautogui.click(pos.x, pos.y)  # miss-click → pode acionar Menu Iniciar

# ✅ CORRETO — paridade 1:1 com coordenadas físicas
from pynput.mouse import Controller, Button
mouse = Controller()
mouse.position = (pos.x, pos.y)
mouse.click(Button.left, 1)
```

**Calibração de coordenadas:** Sempre use `pynput.mouse.Listener` para capturar posições, não `pyautogui.position()`.

### Subprocess sem Popup (clip.exe e similares)
```python
# ✅ Evita que janelas CMD roubem o foco da automação
subprocess.run(['clip.exe'], input=texto, creationflags=subprocess.CREATE_NO_WINDOW)
```

- KI de referência completo: `knowledge/supply_buyer_skip/artifacts/supply_buyer_skip.md`
