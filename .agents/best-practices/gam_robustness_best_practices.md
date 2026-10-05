# 🛡️ Guia de Robustez: Automações GAM

Este manual registra as lições aprendidas sobre a integração entre planilhas Excel (onde o usuário trabalha) e os robôs de automação (onde a precisão é exigida).

## 📊 1. O Problema do "Zero à Esquerda"
O Excel, por padrão, remove os zeros à esquerda quando detecta números (ex: "015" vira "15"). Isso quebrava o robô que esperava 3 dígitos para o ERP.

### Lição Aprendida:
- **Normalização na Inteligência de Busca:** Todo robô de automação (como o `digitador_mix.py`) deve usar o método `.lstrip('0')` em AMBOS os lados da comparação.
- **Exemplo de Código Robusto:**
```python
loja_num = loja_str.lstrip('0')
st_planilha = next((v for k, v in status_map.items() if k.lstrip('0') == loja_num), None)
```
Isso garante que "15" e "015" sejam tratados como a mesma loja (Match Numérico), independente da formatação da planilha.

## 📝 2. Flexibilidade de Nomenclatura (Colunas)
Diferentes planilhas (Mix, Pedido, Ruptura) podem usar cabeçalhos variados como "Descrição", "Produto" ou "Empresa : Produto".

### Lição Aprendida:
- **Detecção Multitermo:** O robô não deve depender de um nome de coluna estrito. Use `any()` para buscar sinônimos.
- **Termos de Sucesso:** `['descri', 'produto', 'nome']`.
- **Efeito:** Garante que o log de execução nunca venha vazio, facilitando a auditoria pelo usuário.

## 🚀 3. Estabilidade do Loop ERP
O robô deve manter-se sincronizado com o ERP mesmo em variações de rede.

### Lição Aprendida:
- **Watchdog e Timeouts:** Manter intervalos de `0.2` a `1.5` segundos entre comandos `F2`, `F8` e `F4` para evitar cliques em telas que ainda não carregaram (Visão Turbo).

## 🥇 4. Regra de Ouro: Exclusividade de CDs
Para evitar conflitos de faturamento, o CD 15 tem prioridade máxima de ativação.

### Lição Aprendida:
- **Logística Blindada:** Se o CD 15 for marcado como **Ativo (A)**, o robô deve forçar **Inativo (I)** nos CDs 16 e 50, ignorando qualquer outra instrução para eles.
- **Hierarquia:** Configuração de Negócio > Planilha.

## 👥 5. Agrupamentos Dinâmicos (G, M, P)
A manutenção de mix agora suporta siglas para agilizar a digitação de grandes volumes de lojas.

### Lição Aprendida:
- **Classificação Baklizi:** 
    - **G (Grandes):** 002, 003, 006, 011, 012, 017, 018.
    - **M (Médias):** 013, 014.
    - **P (Pequenas):** 004, 005, 007, 008.
- **Comando Combinado:** A coluna Loja indica o **alvo** (ex: "GM") e a coluna Status indica a **ação** (A/I). Isso torna o robô condicionado à intenção do usuário naquela linha.

## 🧹 6. Hierarquia de Inativação (TI)
Diferenciar ordens globais de ordens totais evita inativações acidentais em centros de distribuição.

### Lição Aprendida:
- **TI Global (Loja Vazia):** Inativa todas as lojas de varejo, mas **preserva** os CDs.
- **TI Total (Código "CD"):** Inativa todas as lojas **e** todos os CDs.

## 🎯 7. Isolamento de OCR e Prevenção de Falsa Seleção Inversa (Anti Auto-Detecção)
Quando o robô faz OCR de tela cheia para buscar palavras como `SELECAO INVERSA` ou `PULMAO`, ele pode ler a sua própria interface (janela do GAM, logs, lista de ações).

### Lição Aprendida:
- **Regra:** Nunca capturar tela inteira para OCR de alertas. Isole a captura estritamente nas coordenadas da janela modal ativa (`win32gui.GetWindowRect(win32gui.GetForegroundWindow())`) ou na região central do ERP, ignorando totalmente a tela do GAM.

## ⚠️ 8. Diferenciação Semântica de Popups Delphi ("Atenção")
O Consinco utiliza a mesma janela com título "Atenção" para dezenas de mensagens diferentes (ex: caracteres especiais na descrição vs pergunta de seleção inversa).

### Lição Aprendida:
- **Regra:** Não assuma que "Atenção" significa Seleção Inversa. Leia o corpo do texto via OCR:
  - Se for aviso de acentuação/caracteres especiais: confirme com `Enter` e prossiga normalmente.
  - Se for *"Deseja configurar a seleção inversa?"*: entre no fluxo de correção de abastecimento/pulmão.

---
*Manual atualizado com lições de isolamento de visão computacional e resiliência de grid.*
*Data: 03/10/2026.*
