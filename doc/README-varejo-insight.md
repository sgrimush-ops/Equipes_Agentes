# Squad Varejo Insight

Especializada em inteligência de abastecimento, gestão de estoque e automação de pedidos para redes de varejo.

> **Última atualização:** 31/03/2026

---

## 👥 Agentes e Responsabilidades

| Agente | Papel | Responsabilidade Principal |
|--------|-------|---------------------------|
| 🤵 **Danilo Dados** | Analista de Dados | Processa giros de estoque, calcula ROP com lead time dinâmico (2–4 dias) e sugere reposições com base no saldo do CD |
| 👸 **Gabi Gôndola** | Visual Merchandising | Garante estética e "efeito de massa"; aplica travas de estoque mínimo de apresentação (facing) |
| 📦 **Leonardo Logística** | Logística de Loja | Identifica sobras no depósito da loja para evitar pedidos desnecessários ao CD |
| 🌤️ **Clara Clima** | Inteligência Sazonal | Ajusta OTB (Open-to-Buy) com base em previsões climáticas e histórico promocional |
| 🛒 **Paulo Pedidos** | Gestor do CD | Gerencia o "Estoque Pulmão" no **CD (Filial 15)**; cobertura de 15 dias para a rede |
| 📊 **Roberta Relatórios** | Relator Executivo | Consolida KPIs estratégicos e alertas de ação para a diretoria |

---

## ⚙️ Regras de Negócio Implementadas

1. **CD Centralizado:** A Filial 15 é o hub oficial de distribuição.
2. **Lead Time Dinâmico:** Ciclo de reposição entre 2 e 4 dias.
3. **Padrão de Segurança CD:** Manutenção de 15 dias de giro global no CD.
4. **Conversão de Embalagem:** Ordens de compra para o CD usam a unidade do fornecedor (caixas/fardos).
5. **Min/Max em Caixas:** `ESTQMINIMO` e `ESTQMAXIMO` do Consinco são armazenados em caixas. Sempre multiplicar por `EMBL_COMPRA` antes de comparar com estoque em unidades.
6. **EAN/DUN como Texto:** Ao exportar identificadores ao Google Sheets, forçar formato `TEXT` via API para preservar zeros à esquerda.
7. **Filtro de Ativos:** Sync de EAN/DUN filtra apenas produtos com estoque atual ou venda nos últimos 90 dias.

---

## 🗂️ Pipelines e Módulos

### 📈 Dashboard de Ruptura

| Item | Detalhe |
|------|---------|
| Script | `Aplicativos/ruptura/rp.py` |
| Output | `dashboard_ruptura_AAAA-MM-DD.html` (< 10MB) |
| Arquitetura | No-Server: JSON embutido + filtros JavaScript client-side |
| Snapshots | Histórico diário em `ruptura/historico_ruptura/` |
| Filtros UI | Loja + Comprador; botões "Totais Gerais" / "Só Compradores" |
| Fonte de dados | `import_querys/query.parquet` |

### 📊 Pipeline EAN/DUN → Google Sheets

```
ean_dun.txt (Consinco)
    ↓ barras.py          → ean_dun.parquet (Parquet estruturado)
    ↓ sync_google_sheet.py → Google Sheets (EAN/DUN como TEXT)
                              (filtrado para produtos ATIVOS)
```

| Script | Pasta | Função |
|--------|-------|--------|
| `barras.py` | `import_querys/` | Converte `ean_dun.txt` → `ean_dun.parquet` |
| `sync_google_sheet.py` | `import_querys/` | Envia EAN/DUN ao Sheets (formato TEXT, filtrado) |
| `sync_appsheet.py` | `import_querys/` | Integração com AppSheet via REST |
| `sync_projetobak.py` | `import_querys/` | Push automático de `query.parquet` para GitHub |

### 🤖 Automação GAM — Robô Supply

| Item | Detalhe |
|------|---------|
| Script | `GAM/actions/acao_digitar_pedido_supply.py` |
| Skip Logic | Lê comprador via clipboard antes de atribuir; pula se já for "SUPPLY" |
| Verificação Pós-F3 | Confere comprador após salvar e corrige via Up/Down + F4 |
| Clique Calibrado | `pynput.mouse.Controller` (nunca `pyautogui`) — compatível com DPI escalado |
| Subprocess | `CREATE_NO_WINDOW` obrigatório (evita roubo de foco) |

### 📦 Min/Max de Estoque

| Script | `min_e_max/acao_preparar_manual_supply.py` |
|--------|------------------------------------------|
| Lógica | `estoque_disponivel (unid) < ESTQMINIMO × EMBL_COMPRA` |
| Estoque disponível | `ESTQLOJA + ESTQDEPOSITO - QTDRESERVADAVDA - QTDRESERVADARECEB` |

---

## 🚀 Como Executar

```
/run-varejo
```

Ou pelo menu principal:
1. Digite `/Equipes_agentes`
2. Selecione **Executar squad**
3. Escolha **varejo-insight**

---

## 🔗 Referências

- [Protocolo Mestre](../.agents/rules.md)
- [Mapa de Projetos](../.agents/resumo_projetos.md)
- [Pipeline EAN/DUN KI](../../.gemini/antigravity/knowledge/ean_sheets_texto/artifacts/ean_sheets_texto.md)
- [Supply Buyer Skip KI](../../.gemini/antigravity/knowledge/supply_buyer_skip/artifacts/supply_buyer_skip.md)
- [Min/Max Unidades vs Caixas KI](../../.gemini/antigravity/knowledge/minmax_unidades_caixas/artifacts/minmax_unidades_caixas.md)
