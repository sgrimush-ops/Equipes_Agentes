# Var-F7 - Confronto de Compras vs Devoluções e Incineração/Perdas

## Query Vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/confronto_compras_vs_incineracao_perdas.sql`

## Objetivo
Realizar a **auditoria de perdas e descartes sem ressarcimento** comparando as **Compras de Fornecedores (`MLF_NOTAFISCAL`)** contra as **Devoluções/Trocas com Ressarcimento (802, 860)** e as **Incinerações/Avarias sem Ressarcimento (821, 831)** em toda a rede.

### Regra de Negócio Implementada:
1. **Unificação das Empresas (`:LT3`)**: O filtro `:LT3` controla simultaneamente as compras, devoluções e incinerações de todas as lojas e CDs parametrizados (ou `TODOS`), eliminando a necessidade de manter variáveis separadas.
2. **Descarte sem Ressarcimento (821 / 831)**: A query vincula o produto (`SEQPRODUTO` / `SEQFAMILIA`) ao seu Fornecedor Principal e Rede Comercial (`MAP_FAMFORNEC` / `GE_REDE`), desconsiderando que a NF de incineração foi emitida para a própria filial, permitindo apurar exatamente o percentual do que foi comprado e virou lixo/prejuízo sem ressarcimento.
3. **Controle Parametrizado de CGOs de Entrada (`:LT2`)**: Permite selecionar exatamente os CGOs de entrada a confrontar (ex: compras normais `1,28` ou incluindo trocas `34` ou todos `1,2,3,4,6,7,8,28,34,100,101,290`).

---

## Estrutura das Colunas de Resultado

1. **`DEPARTAMENTO`**: Categoria Nível 1 (ex: `LATICINIOS`, `CARNES`, etc.).
2. **`COMPRADOR`**: Comprador responsável pela linha do produto.
3. **`REDE`**: Rede comercial do fornecedor (`GE_REDE`).
4. **`CODIGO_FORNECEDOR`**: Código do Fornecedor Principal (`MAP_FAMFORNEC`).
5. **`FORNECEDOR`**: Razão social do fornecedor de origem.
6. **`CODIGO_PRODUTO`**: Código do produto (`SEQPRODUTO`).
7. **`DESCRICAO_PRODUTO`**: Descrição completa do produto.
8. **`CGO_COMPRA`**: Código Geral de Operação da entrada de compras/transferência de CD (ex: `1`, `28`, `34`, etc. ou `'--'`).
9. **`CGO_SAIDA`**: Código Geral de Operação de saídas/perdas/devoluções do filtro `#LT1` (ex: `802`, `821`, `831`, `860` ou múltiplos separados por vírgula).
10. **`QUANTIDADE_COMPRADA`**: Quantidade total que entrou no período.
11. **`VALOR_COMPRAS`**: Valor total comprado de mercadoria no período.
12. **`QTD_DEVOLVIDA_RESSARCIDA`**: Quantidade devolvida/trocada com nota para o fornecedor (CGO 802/860).
13. **`VLR_DEVOLUCAO_RESSARCIDA`**: Valor devolvido/trocado que gerou crédito financeiro (`DEVREC`).
14. **`QTD_INCINERACAO_PERDA`**: Quantidade incinerada/descartada no lixo/avaria (CGO 821/831).
15. **`VLR_INCINERACAO_PERDA`**: **Valor do prejuízo descartado sem ressarcimento de fornecedor**.
16. **`VLR_TOTAL_PERDAS_DEV`**: Soma de Devoluções + Incinerações.
17. **`SALDO_LIQUIDO_ESTOQUE`**: Saldo líquido que sobrou para venda (`Compras - Devoluções - Incinerações`).
18. **`PERC_INCINERACAO_SOBRE_COMPRA`**: **% de Incineração sobre o Comprado** (`(VLR_INCIN / VLR_COMPRAS) * 100`).
19. **`PERC_TOTAL_PERDA_SOBRE_COMPRA`**: % Total de perda/devolução sobre o comprado.

---

## Variáveis para Cadastrar em Var - F7 (6 Variáveis)

| Ordem | Variável | Tipo | Tipo de Retorno | Descrição na Tela | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|---|---|
| 1 | **`#LT1`** | Macro | - | CGOs de Saída | `802,860,831,821` | Informe os CGOs de devolução e descarte separados por vírgula |
| 2 | **`LT2`** | Literal | Literal | CGOs Entrada | `1,2,3,4,6,7,8,28,34,100,101,290` | Informe os CGOs de entrada desejados ou `0` para todos |
| 3 | **`LT3`** | Literal | Literal | Empresas | `1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,9,21,50,900` | Informe as lojas/CDs desejadas ou digite `TODOS` |
| 4 | **`LT4`** | Literal | Literal | Codigo Fornecedor | `0` | Informe o código do fornecedor ou deixe `0` para todos |
| 5 | **`DT1 / DT2`** | Data | - | Data Inicial / Final | `01/09/2026` a `09/09/2026` | Período de apuração |
| 6 | **`LS1`** | Lista | Literal | REDE | ` TODAS AS REDES` | Selecione a Rede (`GE_REDE`) desejada ou mantenha ` TODAS AS REDES` |

---

## SQL da Lista LS1 (Rede)
Cole o script SQL abaixo no cadastro da variável `LS1` dentro de **Var - F7** (limite de 145 caracteres):

```sql
SELECT ' TODAS AS REDES' FROM DUAL UNION ALL SELECT DESCRICAO FROM GE_REDE
```
