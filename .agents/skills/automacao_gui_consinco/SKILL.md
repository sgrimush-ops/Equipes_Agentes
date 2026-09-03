---
name: Automação GUI e Leitura Visual Consinco (OCR & PyInstaller)
description: Boas práticas para automação de interface gráfica, calibração de grid, leitura OCR no ERP Consinco com RapidOCR e empacotamento PyInstaller portátil (sem instalação).
---

# Automação GUI, Calibração de Grid e OCR Portátil no ERP Totvs Consinco

Esta skill condensa as melhores práticas e padrões arquiteturais validados em produção/prototipação para criar robôs portáteis (`No-Install / Pendrive`) de automação na interface desktop do ERP Totvs Consinco.

---

## 1. Motor OCR Portátil: RapidOCR vs Tesseract
Para distribuir executáveis em Pendrive sem exigir instalação de binários ou drivers de OCR na máquina do usuário final:
- **Use `rapidocr_onnxruntime`**: É 100% nativo em Python/C++ via ONNX Runtime e não necessita de instaladores externos no Windows.
- **Evite Tesseract (`pytesseract`) em modo portátil**: Exige `tesseract.exe` instalado localmente ou binários pesados e configuração complexa de PATH/TESSDATA.

### Empacotamento Crítico com PyInstaller + RapidOCR
Ao empacotar projetos que utilizam `rapidocr_onnxruntime`, o PyInstaller **não consegue detectar automaticamente** as importações dinâmicas (`importlib`) dos detectores e reconhecedores (`ch_ppocr_v3_det`, `ch_ppocr_v3_rec`, `ch_ppocr_v2_cls`). Se os submódulos não forem adicionados explícitamente em `hiddenimports`, o build não emitirá erro, mas o `.exe` falhará em tempo de execução com:
`AttributeError: module 'ch_ppocr_v3_det' has no attribute 'TextDetector'`

**Estrutura obrigatória no arquivo `.spec`:**
```python
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas_list = [('core', 'core'), ('Dados', 'Dados')]
hidden_imports_list = [
    'pyautogui', 'pynput', 'pynput.mouse._win32', 'pynput.keyboard._win32',
    'pyperclip', 'PIL', 'PIL.ImageGrab', 'cv2', 'rapidocr_onnxruntime',
    'pyclipper', 'shapely', 'onnxruntime', 'tkinter'
]

# Coleta tanto os modelos .onnx (data files) quanto todos os 12+ submódulos internos python
try:
    datas_list += collect_data_files('rapidocr_onnxruntime')
    hidden_imports_list += collect_submodules('rapidocr_onnxruntime')
except Exception:
    pass

a = Analysis(
    ['app.py'],
    datas=datas_list,
    hiddenimports=hidden_imports_list,
    ...
)
```

---

## 2. Calibração de Caixas OCR na Tabela do Consinco (Evitando Coluna de Data)
Na tela **Quitação de Título** e tabelas similares do Consinco, o campo **Valor em Aberto / Vlr/Acresc de** fica imediatamente à direita da coluna de **Data de Vencimento** (ex: `11/03/2026` logo à esquerda de `37,44`).

- **Problema comum:** Caixas de captura (`Bounding Boxes`) centralizadas e largas à esquerda (ex: `x_valor - 40` até `x_valor + 40`) invadem visualmente a coluna da esquerda, fazendo o OCR misturar o ano (`2026`) com o valor financeiro (`202637.44` ou substituir `19,25` por `2026`).
- **Solução de Estreitamento Assimetricamente à Direita:**
  Corte a caixa rente ao clique ou deslocada à direita (ex: `[x - 20, y - 10, x + 65, y + 10]`, largura total de ~85px e altura de ~20px), garantindo isolamento da coluna alvo.

### Tratamento e Validação Numérica do Texto OCR
Sempre aplique filtragem via Regex para isolar o token financeiro de centavos:
```python
import re

def limpar_e_extrair_valor(texto_raw: str) -> float:
    # Remove caracteres inválidos mantendo dígitos, pontos e vírgulas
    matches = re.findall(r'[\d.,]+', texto_raw)
    if not matches:
        return 0.0
    
    # Procura tokens da direita para a esquerda que possuam duas casas decimais
    for tk in reversed(matches):
        if re.search(r'\d+[.,]\d{2}$', tk):
            val_clean = tk.replace('.', '').replace(',', '.') if ',' in tk and '.' in tk else tk.replace(',', '.')
            try:
                return float(val_clean)
            except ValueError:
                continue
    
    # Fallback no último token numérico encontrado
    try:
        return float(matches[-1].replace(',', '.'))
    except ValueError:
        return 0.0
```

---

## 3. Mecânica de Navegação e Ancoragem na Tabela Consinco (Seta para Baixo)
As tabelas do Consinco exibem um número fixo de linhas visíveis por vez no grid (ex: 12 linhas, da Linha 1 no topo até a Linha 12 na base).

- **Comportamento da Rolagem via Teclado (`pyautogui.press('down')`):**
  - Do degrau 1 ao 12 (`step 0` a `step 11`), o pressionamento da seta para baixo desce fisicamente o foco para a próxima linha visível (`Y = linhas_y[step]`).
  - A partir da 12ª linha (`step >= 12`), o foco visual do Consinco **permanece travado na 12ª linha** (`Y = linhas_y[11]`), enquanto os registros ocultos sobem na tela para essa mesma posição.
- **Regra de Ancoragem para Cliques e Leitura OCR:**
  ```python
  if step < len(linhas_y):
      linha_visivel_idx = step          # Desce fisicamente até a linha 12
  else:
      linha_visivel_idx = len(linhas_y) - 1  # Permanece travado na linha 12 (Y final)
  
  y_atual = int(linhas_y[linha_visivel_idx])
  ```

---

## 4. Proteção de Arquivos e Acompanhamento Financeiro na GUI

1. **Proteção contra Arquivos Ocultos de Bloqueio do Excel (`~$`):**
   Quando o usuário abre o Excel (`conferencia.xlsx`) para acompanhar a automação ao vivo, o Windows cria o arquivo oculto `~$conferencia.xlsx`. Os scripts de empacotamento e leitura devem obrigatoriamente filtrar arquivos iniciados com `~$` e `.` para evitar `PermissionError`.
2. **Paridade Financeira ao Vivo na Interface Gráfica:**
   Para validação em tempo real ao lado da janela do Consinco, a GUI sobreposta (`-topmost`) deve manter largura otimizada (`~640px`) e exibir um painel dinâmico somando centavo por centavo os itens validados:
   `💰 VALOR SOMADO MARCADO: R$ X.XXX,XX`
   Isso permite que o operador compare instantaneamente a soma do robô com o campo `Vlr Pagar/Rec.` e `Total Pagar/Rec.` do ERP Consinco.

---

## 5. Automação de Células com ComboBox e Grids Delphi (Manutenção de Mix / Logística)

Ao automatizar grids com componentes de edição embutidos (`TDBGrid` / `TComboBox` no Consinco):

1. **Ciclo de Ativação Obrigatório de Setas (`Down` -> `Up`) no ComboBox:**
   - No componente `TComboBox` do Delphi, se a lista for aberta mas nenhuma tecla de seta for pressionada, o componente não dispara o evento `OnChange`/seleção de índice. Ao teclar `Tab`, o campo permanece nulo/vazio (gerando erro de *"A Embalagem deve ser informada"*).
   - **Padrão Obrigatório de Seleção:**
     - Abrir o dropdown com `Alt + Down`.
     - Enviar `Down` obrigatoriamente para registrar a alteração de índice.
     - Se a embalagem correta for a primeira da lista (ex: `DP 60`), enviar `Up` para retornar ao topo com a opção já ativada.
     - Se for outra opção (ex: `CX 24` em vez de `CX 12`), continuar descendo com `Down` até o OCR validar o texto ativo em azul (`blue_mask > 25`).
2. **Proibição de Teclar `Enter` no Grid:**
   - Nunca tecle `Enter` para confirmar o ComboBox no grid do Consinco, pois o `Enter` pode fechar a edição ou pular de linha.
   - Pressione diretamente **`Tab`**, que no Consinco confirma o ComboBox e avança imediatamente o cursor para a coluna seguinte (**Lastro**).
3. **Limpeza Prévia de Valores Residuais / Sugeridos (Prevenção de `60100`):**
   - Ao teclar `Tab` saindo da Embalagem, o Consinco frequentemente preenche o campo de Lastro com o multiplicador da embalagem (ex: `60`).
   - Digitar diretamente faz o robô concatenar o valor (`60100` em vez de `100`).
   - **Solução Obrigatória:** Antes de digitar em cada célula numérica (`Lastro`, `Altura`, `Estoque Mínimo`), enviar `Backspace` (x4) e `Delete` (x4) para limpar qualquer texto residual antes de executar o `pyautogui.write()`.
4. **Fechamento Condicional de Popups Modais (`Alt + O`):**
   - No disparo de popups ao salvar (ex: Seleção Inversa pendente), fechar o 1º popup com `Alt + O` e usar `win32gui.GetWindowText(GetForegroundWindow())` para verificar se existe o 2º popup antes de enviar novo comando, evitando `Alt + O` excedente.
5. **Gravação e Auditoria Visual Passo a Passo:**
   - Instrumentar métodos críticos com salvamento de screenshots destacando o ponto de clique com alvo vermelho (`cv2.circle`) e arquivo de log cronológico para rastreamento de falhas de foco e grid.
6. **Varredura Dinâmica do Grid (Apanha vs Pulmão) para Identificação de Embalagem:**
   - Em grids logísticos do Consinco (*Espécie de Endereço*), a embalagem oficial do produto frequentemente está expressa na linha `APANHA` (ex: `CX 120`) e visualmente omitida ou herdada na linha `PULMAO`.
   - **Proibição de Valores Padrão Hardcoded:** Nunca assuma embalagens padrão (ex: `DP 60`). Realize uma varredura OCR completa na área do grid (`y: 670 a 750`) com regex `(CX|DP|UN|FD|PCT|PC|CJ|KG|LT)\s*\.?\s*\d+` abrangendo tanto Apanha quanto Pulmão. Isso assegura que o robô busque a embalagem real do produto no ComboBox (ex: `CX 120` em vez de falhar e selecionar `UN 1` por timeout).

