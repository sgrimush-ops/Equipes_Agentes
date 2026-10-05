# Aprendizado Técnico: Fechamento Operacional do Supply em Lote e Filtros de Data Resilientes (PostgreSQL / SQLite)

## 📌 Contexto e Diagnóstico

Durante a operação do módulo de campanhas e da consulta de histórico de pedidos no ecossistema Baklizi:
1. **Erro 500 no Fechamento do Supply (`supply-finalizar`):** O frontend Web App enviava uma lista consolidada com a matriz de 14 lojas de múltiplos itens (`dados_fechamento`), mas os endpoints `supply-fechamento` e `supply-finalizar` repassavam diretamente para funções que esperavam parâmetros individuais de apenas um item, gerando `TypeError` no FastAPI e estouro de erro no frontend (`Unexpected token 'I', "Internal S"... is not valid JSON`).
2. **Inversão e Falha no Filtro de Data do Histórico:** Ao filtrar por uma data específica (ex: 05/10/2026 a 05/10/2026), a consulta retornava 1000 pedidos (atingindo o teto `LIMIT 1000`) ou excluía os pedidos do próprio dia.

---

## 🔍 Causas Raízes e Lições Aprendidas

### 1. Persistência em Lote de Matriz Multilojas do Supply
- **Assinatura vs Payload:** No Web App moderno, o usuário visualiza todos os produtos da campanha lado a lado e digita as caixas de todas as 14 lojas em um único grid interativo.
- **Padrão de Fechamento em Lote:** É mandatório criar funções especializadas para processamento em lote (`salvar_fechamento_supply_lote`), agrupando os registros por `item_id`, calculando as caixas de transferência (`cx_transf`), multiplicando pela embalagem (`embalagem_transferencia`), apurando o estoque em tempo real do CD15 (`QUANTIDADE_DISPONIVEL` do `query.parquet`) e gerando/limpando pendências em `campanha_devolutivas` antes de transicionar o status da campanha para `FINALIZADA` ou `PENDENCIA_COMPRAS`.

### 2. A Armadilha Lexicográfica de Strings ISO com `'T'` em SQL
- **Problema de Comparação Textual:** Quando colunas de data/hora são gravadas como texto no formato ISO 8601 (ex: `'2026-10-05T11:46:00'`) ou timestamps com timezone, uma cláusula SQL do tipo:
  ```sql
  WHERE data_pedido <= '2026-10-05 23:59:59'
  ```
  falha catastroficamente porque o caractere `'T'` (ASCII 84) é maior que o caractere de espaço `' '` (ASCII 32). Portanto, `'2026-10-05T...' <= '2026-10-05 ...'` resulta em **FALSE**, descartando todos os registros do dia consultado.
- **Soberania do Evento:** Em relatórios de histórico (ex: Histórico de Pedidos Aprovados), a coluna de filtragem deve ser a data em que a aprovação ocorreu (`data_aprovacao`), utilizando `COALESCE(data_aprovacao, data_pedido)` como fallback.
- **Solução Universal:**
  - **PostgreSQL:** `CAST(COALESCE(data_aprovacao, data_pedido) AS DATE) >= CAST(:dta_ini AS DATE)`
  - **SQLite:** `substr(replace(COALESCE(data_aprovacao, data_pedido), 'T', ' '), 1, 10) >= :dta_ini`

### 3. Auto-Ajuste de Intervalos Invertidos
- Se o usuário selecionar acidentalmente uma Data Início maior que a Data Fim (ex: 05/10/2026 a 01/10/2026), o sistema deve ordenar automaticamente `d_ini, d_fim = min(d_ini, d_fim), max(d_ini, d_fim)` no backend e frontend, evitando frustração com retornos vazios.

---

## 🛠️ Arquivos de Referência
- [`services/campanha_service.py`](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/APP_Bak/services/campanha_service.py) — Funções `obter_mapa_estoque_cd15_produtos`, `salvar_fechamento_supply_lote` e `finalizar_avaliacao_campanha`.
- [`api/campanhas.py`](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/APP_Bak/api/campanhas.py) — Rotas `/supply-fechamento` e `/supply-finalizar`.
- [`api/pedidos.py`](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/APP_Bak/api/pedidos.py) — Função `montar_clausulas_historico` e rotas de histórico/exportação.
- [`static/js/app.js`](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/APP_Bak/static/js/app.js) — Funções `finalizarAvaliacaoSupply`, `carregarHistoricoAprovados` e `toggleDestaqueLinhaTabela`.
