# Aprendizado de Performance: Padrão Oficial de Vendas via `MRL_CUSTODIA` e Otimização de Rankings

## 1. Contexto e Motivação
Em relatórios de Ranking Comercial, Giro, Vendas por Fornecedor/Comprador e Curva ABC no Totvs Consinco:
- **Anti-padrão anterior:** Varrer tabelas e views de documentos fiscais item a item (`MLFV_BASENFE` + `MFLV_BASEDFITEM` ou `MFL_DOCTOFISCAL` + `MFL_DFITEM`) filtrando CGOs de venda (800, 810, 848).
- **Problema:** Em bases com dezenas de lojas e milhões de itens emitidos diariamente, a varredura fiscal gera *Full Table Scans* e *Hash Joins* pesadíssimos, levando a travamentos ou minutos de espera até para períodos curtos (ex: 2 dias).

---

## 2. Padrão Oficial: Vendas Consolidadas via `MRL_CUSTODIA`
A tabela **`MRL_CUSTODIA`** é a base oficial de fechamento diário do ERP Totvs Consinco. Nela, as vendas já estão sumarizadas e apuradas por Dia (`DTAENTRADASAIDA`), Loja (`NROEMPRESA`) e Produto (`SEQPRODUTO`).

### Vantagens:
1. **Velocidade:** Reduz o volume de leitura em mais de **95%**, baixando o tempo de execução de minutos para milissegundos.
2. **Confiabilidade:** É a mesma fonte utilizada pelas telas nativas do Consinco (`Consulta Produtos -> Histórico` e Curva ABC).
3. **Métricas Prontas:**
   - Valor Total Faturado em R$: `SUM(NVL(V.VLRTOTALVDA, 0))`
   - Volume/Quantidade Vendida: `SUM(NVL(V.QTDVDA, 0))`

### Bloco Padrão de Vendas na Query:
```sql
SELECT PR.FORN_PRINCIPAL_COD AS CODIGO_FORNECEDOR,
       PR.FORN_PRINCIPAL_NOME AS FORNECEDOR,
       PR.COMPRADOR,
       PR.SEQPRODUTO,
       SUM(NVL(V.VLRTOTALVDA, 0)) AS VLR_VENDA,
       0 AS VLR_COMPRA, 
       0 AS VLR_BONIFICADO, 
       0 AS VLR_DEVOLUCAO_COMPRA, 
       0 AS VLR_TROCA_COMPRA, 
       0 AS VLR_CUSTO_CD, 
       0 AS VLR_CUSTO_LOJAS, 
       0 AS QTD_INCINERACAO_ANO
  FROM MRL_CUSTODIA V
  JOIN PRODUTOS_FILTRADOS PR ON PR.SEQPRODUTO = V.SEQPRODUTO
 WHERE V.DTAENTRADASAIDA >= TRUNC(:DT1) 
   AND V.DTAENTRADASAIDA < TRUNC(:DT2) + 1 
   AND V.NROEMPRESA IN (1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,50)
 GROUP BY PR.FORN_PRINCIPAL_COD, PR.FORN_PRINCIPAL_NOME, PR.COMPRADOR, PR.SEQPRODUTO
```

---

## 3. Padrão de Fusão dos Documentos de Saída (Devolução, Troca e Incineração)
Quando for necessário auditar movimentações fiscais de saída (Devolução de Compra `CGO 802`, Troca `CGO 860`, Incineração/Descarte `CGO 821, 831`):
- **NUNCA** crie múltiplos blocos de `UNION ALL` lendo `MLFV_BASENFE` / `MFLV_BASEDFITEM` separadamente.
- **SEMPRE** unifique em uma **única leitura** agrupada usando `CASE WHEN CODGERALOPER IN (...)`:

```sql
SELECT PR.FORN_PRINCIPAL_COD AS CODIGO_FORNECEDOR,
       PR.FORN_PRINCIPAL_NOME AS FORNECEDOR,
       PR.COMPRADOR,
       PR.SEQPRODUTO,
       0 AS VLR_VENDA, 
       0 AS VLR_COMPRA, 
       0 AS VLR_BONIFICADO, 
       SUM(CASE WHEN N.CODGERALOPER = 802 THEN NVL(I.VLRITEM, 0) + NVL(I.VLRIPI, 0) + NVL(I.VLRICMSST, 0) ELSE 0 END) AS VLR_DEVOLUCAO_COMPRA,
       SUM(CASE WHEN N.CODGERALOPER = 860 THEN NVL(I.VLRITEM, 0) + NVL(I.VLRIPI, 0) + NVL(I.VLRICMSST, 0) ELSE 0 END) AS VLR_TROCA_COMPRA,
       0 AS VLR_CUSTO_CD, 
       0 AS VLR_CUSTO_LOJAS, 
       SUM(CASE WHEN N.CODGERALOPER IN (821, 831) AND NVL(N.MODELO,'0') <> '65' THEN NVL(I.VLRITEM,0) ELSE 0 END) AS QTD_INCINERACAO_ANO
  FROM MLFV_BASENFE N
  JOIN MFLV_BASEDFITEM I ON I.SEQNF = N.SEQNF AND I.NROEMPRESA = N.NROEMPRESA AND I.TIPNOTAFISCAL = N.TIPNOTAFISCAL
  JOIN PRODUTOS_FILTRADOS PR ON PR.SEQPRODUTO = I.SEQPRODUTO
 WHERE N.TIPNOTAFISCAL = 'S'
   AND N.CODGERALOPER IN (802, 860, 821, 831) 
   AND N.DTAEMISSAO >= TRUNC(:DT1) 
   AND N.DTAEMISSAO < TRUNC(:DT2) + 1 
   AND N.STATUSNF != 'C' 
   AND N.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 21, 50)
 GROUP BY PR.FORN_PRINCIPAL_COD, PR.FORN_PRINCIPAL_NOME, PR.COMPRADOR, PR.SEQPRODUTO
```

---

## 4. Padrão de Posição de Estoque e Custos (`MRL_PRODUTOEMPRESA`)
Os valores de saldo de estoque atual e custo médio unitário são extraídos da **`MRL_PRODUTOEMPRESA`**:
- **Estoque Físico Total:** `(NVL(PE.ESTQLOJA, 0) + NVL(PE.ESTQDEPOSITO, 0))`
- **Custo Médio da Última Entrada com Impostos:** `(NVL(PE.CMULTVLRNF, 0) + NVL(PE.CMULTIPI, 0) + NVL(PE.CMULTICMSST, 0) + NVL(PE.CMULTDESPNF, 0) + NVL(PE.CMULTDESPFORANF, 0))`
- **Separação CD vs Lojas:**
  - CD: `NROEMPRESA IN (15, 16, 50)`
  - Lojas: `NROEMPRESA IN (1,2,3,4,5,6,7,8,11,12,13,14,17,18)`
