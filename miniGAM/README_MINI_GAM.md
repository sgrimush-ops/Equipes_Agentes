# ⚡ Mini-GAM — Protótipo de Automação e Validação de Checklists (Consinco)

O **Mini-GAM** é uma solução compacta e autônoma desenvolvida com base nos aprendizados do ecossistema GAM (Gerenciador de Automações e Macros) e na skill de Visão Avançada (`pynput` calibrado para paridade de cliques 1:1 no Windows), projetada especificamente para rodar diretamente de um **Pendrive**.

---

## 🚀 Funcionalidades Principais

1. **Interface Sobreposta (`-topmost`)**: Fica flutuando acima de todas as telas do sistema e do ERP Consinco, permitindo controle visual sem perder o foco na operação.
2. **Botão `🎯 MAPEAR CHECKLIST`**:
   - Assistente visual inteligente que guia a calibração com 4 cliques rápidos:
     1. Coluna **Título** na Linha 1.
     2. Coluna **Valor em Aberto** na Linha 1.
     3. Coluna **Checkbox (Qui)** na Linha 1.
     4. Coluna **Checkbox (Qui)** ou centro da **Linha 12 (última visível)**.
   - A partir das Linhas 1 e 12, o algoritmo **calcula automaticamente as 12 coordenadas equidistantes** de todas as linhas visíveis do grid.
3. **Botão `▶ COMEÇAR`**:
   - Inicia uma **contagem regressiva de 5 segundos**, dando tempo ao operador para ativar e posicionar o foco na janela "Quitação de Título" do Consinco.
   - **Validação em duas fases**: o robô executa uma primeira passada descendo pela lista e, em seguida, faz uma segunda passada subindo para re-checar itens pendentes e recuperar registros que possam ter sido perdidos na primeira varredura.
   - **Comparação com a planilha**: ele lê cada linha da tela, cruza o título com a planilha Excel em `Dados/conferencia.xlsx` e valida o valor. Quando há coincidência, clica no checkbox, marca o item como validado e salva o status em tempo real na coluna **`Marcado`** do Excel.
   - **Parada inteligente**: a execução pode encerrar antes do fim manual quando a soma acumulada dos valores validados alcança o total esperado da planilha (com pequena tolerância) ou quando a segunda fase chega ao topo da tela sem novas mudanças.
   - **Retorno no Excel (`Marcado` = `ok`)**: todas as linhas confirmadas na tela têm seu status gravado na coluna **`Marcado`**. Caso você deixe o Excel aberto e travado durante a execução, o robô salva um backup automático chamado `conferencia_conferido.xlsx` para garantir que nenhum dado se perca.
4. **Botão `⏹ PARAR`**: Interrompe a execução a qualquer momento com segurança.
5. **Modos de Leitura na Tela**:
   - **OCR Visual (`Tesseract + OpenCV` - Padrão e Recomendado)**: Como a tela de Quitação de Título do Consinco **não permite copiar dados (`Ctrl+C`)**, este modo realiza o recorte em tempo real ao redor da coordenada mapeada. Aplica **upscaling de 2.5x**, **inversão inteligente de cor** (para a linha selecionada em fundo preto e texto branco) e **limiar de Otsu**, garantindo leitura perfeita do Título e Valor com máxima nitidez visual.
   - **Clipboard (`Ctrl+C`)**: Modo secundário para telas onde a cópia seja permitida no futuro.

---

## 📂 Estrutura de Arquivos no Pendrive

Ao gerar o executável ou copiar para o Pendrive, a estrutura deve ser:
```text
Mini-GAM_Pendrive/
│
├── Mini-GAM.exe           # Executável principal da interface gráfica
├── Dados/
│   └── conferencia.xlsx  # Planilha Excel com colunas "Titulo" e "Valor"
├── conferencia.csv        # Alternativa CSV (fallback automático)
├── coords_minigam.json    # Criado automaticamente após clicar em Mapear Checklist
└── core/                  # Módulos internos empacotados pelo PyInstaller
```

---

## 🛠️ Como Empacotar para o Pendrive (`PyInstaller`)

Para construir o executável portátil (`Mini-GAM.exe` e pasta `dist/Mini-GAM_Pendrive/`), execute o script de build na raiz de `miniGAM`:

```powershell
python build_minigam.py
```
*(Ou, se preferir via comando direto do PyInstaller)*:
```powershell
python -m PyInstaller --clean -y Mini-GAM.spec
```

O diretório pronto para ser copiado para o seu pendrive será gerado em:
`dist/Mini-GAM_Pendrive/`

---

## 📋 Como Testar Agora Mesmo (Modo Python / Protótipo)

Enquanto estiver no ambiente de desenvolvimento, basta rodar:

```powershell
python Mini-GAM.py
```

1. Clique em **`Selec...`** ou verifique se o arquivo `conferencia.xlsx` (gerado de amostra) foi carregado.
2. Clique em **`🎯 MAPEAR CHECKLIST`** e aponte para a sua tela do Consinco para salvar as coordenadas (ou teste com uma planilha simulada).
3. Clique em **`▶ COMEÇAR`** e observe o log em tempo real!
