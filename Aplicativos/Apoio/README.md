# Painel de Apoio Operacional

Interface gráfica em Python (Tkinter) inspirada nos padrões visuais do **GAM (Gerenciador de Automações e Macros)**, criada para centralizar a execução dos principais scripts de consulta e cálculo de estoque.

---

## 🚀 Funcionalidades e Botões

| # | Ação | Arquivo Alvo / Operação | Comportamento Especial & Interatividade Gráfica |
|---|---|---|---|
| **1º** | **Executar Data Query** | `Aplicativos\import_querys\1-data_query.py` | Executa a extração/conversão de dados em segundo plano com log em tempo real. |
| **2º** | **Executar Mínimo e Máximo** | `Aplicativos\min_e_max\1-min_max.py` | **100% Gráfico:** Abre tela modal solicitando o **Escopo (Todas as Lojas ou Loja Específica)** e o **Filtro de Exportação (Total, Aumentos, Reduções, Ambos)**. Ao término, **abre automaticamente** a **planilha de digitar** (`digitar.xlsx`) e o resultado `ajustepp.xlsx` no Excel. |
| **3º** | **Abrir Planilha de Capacidade** | `Aplicativos\min_e_max\capacidade.xlsx` | Abre a planilha diretamente no Excel nativo do Windows para consulta ou ajuste. |
| **4º** | **Abrir GAM & Fechar Apoio** | `Aplicativos\GAM\gam.py` | Executa o aplicativo principal do GAM em processo desacoplado e encerra o Painel de Apoio. |

---

## 🎛️ Interações Gráficas do Mínimo e Máximo (2º Botão)

O script original `1-min_max.py` solicitava interações no terminal:
1. **Escopo de Processamento**:
   - `[1]` Todas as Lojas (Geral - exceto CDs)
   - `[2]` Loja Específica (com digitação do número da loja, ex: 14)
2. **Tipo de Relatório / Exportação**:
   - `[1]` APENAS sugestões para AUMENTAR (Recomendado)
   - `[2]` TOTAL
   - `[3]` APENAS sugestões para DIMINUIR
   - `[4]` APENAS AUMENTOS e REDUÇÕES

Na nova interface, ao clicar no **2º Botão**, uma **janela modal intuitiva** solicita essas opções por meio de botões de seleção (Radiobuttons) e campo de texto com validação automática, alimentando o script sem necessidade de intervenção manual no terminal!

Além disso, há um campo **"Entrada Terminal"** no rodapé dos logs para responder a qualquer prompt interativo em tempo real.

---

## 🖥️ Como Executar

1. **Pelo arquivo em lote (Recomendado)**:
   - Dê um duplo clique em `iniciar_apoio.bat`.

2. **Via Terminal**:
   ```bash
   cd c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\Apoio
   python app_apoio.py
   ```
