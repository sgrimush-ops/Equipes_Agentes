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
