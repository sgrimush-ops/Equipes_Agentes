# Guia de Aplicativos (Scripts Principais)

Este guia documenta os subdiretórios da pasta `Aplicativos`, explicando o propósito e o script principal de cada módulo.

> **Última atualização:** 31/03/2026

---

## 📁 GAM (Gerenciador de Automações e Macros)
**Script Principal:** `main.py`

Interface gráfica Tkinter de RPA (Robotic Process Automation). O usuário gerencia filas de ações pré-programadas (bloquear tela, digitar pedidos, aprovar manuais etc.) que são executadas sequencialmente como macros robóticas.

**Submódulos importantes:**
- `actions/acao_digitar_pedido_supply.py` — Digitação automatizada de pedidos Supply com **skip logic de comprador** (pula atribuição se já for "SUPPLY") e **verificação pós-F3** (confere e corrige comprador após salvar).
- `actions/acao_digitar_pedido_CD_016.py` — Pedidos para o CD 016.
- `core/vision_engine.py` — Detecção de elementos via OpenCV (multi-scale).
- **Regra crítica:** Cliques calibrados usam `pynput.mouse.Controller` (nunca `pyautogui`) para evitar miss-clicks por DPI em multi-monitor.

---

## 📁 import_querys (Pipeline de Dados ERP)
**Scripts Principais:** `barras.py`, `sync_google_sheet.py`, `data.py`

Central de importação e exportação de dados do ERP Consinco para os sistemas da Squad.

| Script | O que faz |
|--------|-----------|
| `barras.py` | Converte `ean_dun.txt` (4 colunas: `CODIGO_PRODUTO`, `EAN`, `DUN`, `UNIDADE_EMBALAGEM`) → `ean_dun.parquet`. Saneia EAN/DUN para string sem decimal. |
| `sync_google_sheet.py` | Filtra produtos **ativos** do `query.parquet` e sobe ao Google Sheets com EAN/DUN no formato **TEXT** (preserva zeros à esquerda). |
| `sync_appsheet.py` | Integração com AppSheet via REST API usando chaves do `.env`. |
| `sync_projetobak.py` | Push automático do `query.parquet` para o repositório GitHub `ProjetoBak`. |
| `data.py` | Utilitários de manipulação de data para os pipelines. |

**Atenção:** O arquivo `ean_dun.txt` tem separador `;` e encoding `cp1252` (legado Consinco). O `query.parquet` vem do ERP via extração Oracle/Consinco.

---

## 📁 ruptura (Dashboard de Ruptura)
**Script Principal:** `rp.py`

Gera o Dashboard de Ruptura Comercial — painel HTML interativo, autossuficiente e sem servidor (< 10MB).

**Fluxo:**
1. Lê `import_querys/query.parquet` como fonte de dados.
2. Classifica a "culpa" da ruptura entre [CD] e [Loja].
3. Gera `dashboard_ruptura_AAAA-MM-DD.html` com JSON embutido + filtros JavaScript.
4. Salva snapshot diário em `historico_ruptura/` para rastreabilidade.

**Regras arquiteturais:**
- Denominadores globais (Base CD15) nunca são recalculados do filtro de loja.
- Plotly: `active` do `updatemenus` é apenas cosmético; o range real vem do `update_layout`.
- Botões obrigatórios: "Totais Gerais" e "Só Compradores".

---

## 📁 min_e_max (Estoque Mínimo e Máximo)
**Script Principal:** `acao_preparar_manual_supply.py`

Calcula e parametriza estoques mínimos e máximos para a rede de lojas.

**Regra crítica:** `ESTQMINIMO` e `ESTQMAXIMO` no Consinco são em **CAIXAS** (unidade de embalagem), não em unidades avulsas. Sempre converter antes de comparar com o estoque disponível:

```python
min_unidades = ESTQMINIMO * EMBL_COMPRA
estoque_disponivel = ESTQLOJA + ESTQDEPOSITO - QTDRESERVADAVDA - QTDRESERVADARECEB
if estoque_disponivel < min_unidades: gerar_pedido()
```

---

## 📁 integracao_google (APIs Google)
**Script Principal:** `autenticacao_google.py`

Gerencia autenticação OAuth persistente para Google Drive, Gmail e AppSheet.

| Arquivo | Função |
|---------|--------|
| `autenticacao_google.py` | Token OAuth reutilizável (evita re-login) |
| `modulo_drive.py` | Upload/download Google Drive |
| `modulo_gmail.py` | Envio de e-mails via Gmail API |
| `modulo_appsheet.py` | Chamadas REST ao AppSheet |

**Regra:** EAN/DUN enviados ao Sheets como `TEXT` (API `numberFormat: {type: "TEXT"}`). Dados filtrados para produtosativos antes do upload (evita `exceeds grid limits`).

---

## 📁 memoria_squad (Memória Vetorial)
**Script Principal:** `kernel.py`

Camada de inteligência persistente usando ChromaDB. Armazena regras, lições aprendidas e conhecimentos da Squad para recuperação semântica. Garante que o ecossistema "aprenda" com o tempo e não repita erros.

---

## 📁 mcp_squad (Servidor MCP)
**Script Principal:** `office_server.py`

Servidor MCP local que provê interface padronizada para manipulação segura de arquivos Excel e CSV por agentes externos.

---

## 📁 gerenciamento_sql (Queries Oracle/Consinco)
**Script Principal:** `ap.py`

Ambiente assistido para geração de queries Oracle SQL para o ERP TOTVS Consinco. Usa a skill `gerar_consultas_consinco` e o dicionário local `dicionario_consinco.json`.

---

## 📁 consumo (Conversão de Dados)
**Script Principal:** `ap.py`

Lê `consumo.xlsx` e converte para `consumo.parquet` com saneamento de coluna `codigo` (inteiro puro). Motor de importação para análises de consumo.

---

## 📁 cruzamento (Conciliação Gerencial)
**Script Principal:** `ap.py`

Lê arquivos `.parquet` da pasta `bd/` e efetua conciliações gerenciais. Exibe estrutura, colunas e amostra de cada Parquet para debug rápido.

---

## 📁 pendencias (Consolidação de Relatórios)
**Script Principal:** `consolidado.py`

Varre `bd_saida/` buscando `Loja *.xlsx`, concatena todas as abas verticalmente e gera `consolidado.csv` separado por ponto-e-vírgula.

---

## 📁 mix_site (Mix de Produtos)
**Script Principal:** `convert_to_parquet.py`

Lê `con5cod.xlsx` e converte para `con5cod.parquet`. Motor de importação bruta do mix ativo de produtos da rede.

---

> **Nota:** Todos os módulos seguem o [Protocolo Mestre](./../.agents/rules.md) — Pandas, pathlib, openpyxl, try-excepts resilientes e isolamento em Parquet.
