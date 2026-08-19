# Var-F7 - movimentacao_titulos_por_data_movi

## 1. Objetivo da Consulta
Fornecer um relatório de movimentação e quitação de títulos a pagar/receber (`FI_TITULO`), trazendo exclusivamente os títulos que sofreram **movimentação/operação financeira (`FI_TITOPERACAO`) ou quitação no período de `:DT1` a `:DT2`**, em vez de filtrar estaticamente por data de vencimento ou emissão.

## 2. SQL Principal
Arquivo: [Aplicativos/gerenciamento_sql/querys/movimentacao_titulos_por_data_movi.sql](../querys/movimentacao_titulos_por_data_movi.sql)

```sql
SELECT * FROM (
    WITH CTE_OPERACOES AS (
        SELECT /*+ MATERIALIZE */
            O.SEQTITULO,
            MAX(O.DTAOPERACAO) AS MAX_DTAOPERACAO,
            MAX(NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO)) AS MAX_DTAHORAALTERACAO,
            MAX(O.USUALTERACAO) KEEP (
                DENSE_RANK LAST 
                ORDER BY NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO) NULLS FIRST, O.SEQTITOPERACAO
            ) AS USUALTERACAO
        FROM FI_TITOPERACAO O
        WHERE O.OPCANCELADA IS NULL
          AND O.USUCANCELOU IS NULL
          AND (
              TRUNC(O.DTAOPERACAO) BETWEEN :DT1 AND :DT2
              OR TRUNC(NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO)) BETWEEN :DT1 AND :DT2
          )
        GROUP BY
            O.SEQTITULO
    ),
    CTE_TITULOS_MOV AS (
        SELECT /*+ MATERIALIZE */
            T.SEQTITULO,
            T.NROEMPRESA,
            T.SEQPESSOA,
            T.NROTITULO,
            T.NROPARCELA,
            T.CODESPECIE,
            T.DTAVENCIMENTO,
            T.DTAINCLUSAO,
            T.DTAQUITACAO,
            T.VLRNOMINAL,
            T.VLRPAGO,
            T.ABERTOQUITADO,
            T.SITUACAO,
            T.OBSERVACAO,
            OP.USUALTERACAO AS USU_ULT_OPERACAO,
            NVL(OP.MAX_DTAHORAALTERACAO, CAST(T.DTAQUITACAO AS DATE)) AS DTA_ULT_OPERACAO
        FROM FI_TITULO T
        LEFT JOIN CTE_OPERACOES OP
            ON OP.SEQTITULO = T.SEQTITULO
        WHERE T.SITUACAO != 'C'
          AND (
              OP.SEQTITULO IS NOT NULL
              OR (T.DTAQUITACAO IS NOT NULL AND TRUNC(T.DTAQUITACAO) BETWEEN :DT1 AND :DT2)
              OR (T.DTAMOVIMENTO IS NOT NULL AND TRUNC(T.DTAMOVIMENTO) BETWEEN :DT1 AND :DT2)
          )
          AND (
              :LT1 = '0'
              OR T.CODESPECIE IN (
                  SELECT UPPER(TRIM(REGEXP_SUBSTR(:LT1, '[^,]+', 1, LEVEL)))
                  FROM DUAL
                  CONNECT BY REGEXP_SUBSTR(:LT1, '[^,]+', 1, LEVEL) IS NOT NULL
              )
          )
          AND (:NR1 = 0 OR T.NROTITULO = :NR1)
          AND (
              :LT2 = '0'
              OR T.SEQPESSOA IN (
                  SELECT TO_NUMBER(REGEXP_SUBSTR(:LT2, '[^,]+', 1, LEVEL))
                  FROM DUAL
                  CONNECT BY REGEXP_SUBSTR(:LT2, '[^,]+', 1, LEVEL) IS NOT NULL
              )
          )
          AND (
              :LT3 = '0'
              OR T.ABERTOQUITADO IN (
                  SELECT UPPER(TRIM(REGEXP_SUBSTR(:LT3, '[^,]+', 1, LEVEL)))
                  FROM DUAL
                  CONNECT BY REGEXP_SUBSTR(:LT3, '[^,]+', 1, LEVEL) IS NOT NULL
              )
          )
          AND (
              NVL(TRIM(:LT4), '0') IN ('0', 'TODOS', '')
              OR UPPER(TRIM(OP.USUALTERACAO)) IN (
                  SELECT UPPER(TRIM(REGEXP_SUBSTR(:LT4, '[^,]+', 1, LEVEL)))
                  FROM DUAL
                  CONNECT BY REGEXP_SUBSTR(:LT4, '[^,]+', 1, LEVEL) IS NOT NULL
              )
          )
          AND (
              :LS1 = ' TODAS AS REDES'
              OR EXISTS (
                  SELECT 1
                  FROM GE_REDEPESSOA RP
                  JOIN GE_REDE R ON RP.SEQREDE = R.SEQREDE
                  WHERE RP.SEQPESSOA = T.SEQPESSOA
                    AND R.DESCRICAO = :LS1
              )
          )
    )
    SELECT
        T.NROEMPRESA AS EMPRESA,
        T.SEQPESSOA AS FORNECEDOR,
        P.NOMERAZAO AS NOME_FORNECEDOR,
        T.NROTITULO AS NRO_TITULO,
        T.NROPARCELA AS PARCELA,
        T.CODESPECIE AS ESPECIE,
        TO_CHAR(T.DTAVENCIMENTO, 'DD/MM/YYYY') AS DTA_VENCIMENTO,
        TO_CHAR(T.DTAINCLUSAO, 'DD/MM/YYYY') AS DTA_INCLUSAO,
        TO_CHAR(T.DTAQUITACAO, 'DD/MM/YYYY') AS DTA_QUITACAO,
        TO_CHAR(T.VLRNOMINAL, 'FM999G999G990D00', 'NLS_NUMERIC_CHARACTERS='',.''') AS VLR_NOMINAL,
        TO_CHAR(T.VLRPAGO, 'FM999G999G990D00', 'NLS_NUMERIC_CHARACTERS='',.''') AS VLR_PAGO,
        T.ABERTOQUITADO AS STATUS_PAGTO,
        T.SITUACAO AS SITUACAO,
        T.OBSERVACAO AS OBSERVACAO,
        T.USU_ULT_OPERACAO,
        TO_CHAR(T.DTA_ULT_OPERACAO, 'DD/MM/YYYY HH24:MI:SS') AS DTA_ULT_OPERACAO
    FROM CTE_TITULOS_MOV T
    LEFT JOIN GE_PESSOA P
        ON P.SEQPESSOA = T.SEQPESSOA
    ORDER BY
        T.DTA_ULT_OPERACAO DESC NULLS LAST,
        T.DTAVENCIMENTO DESC,
        T.SEQPESSOA
)
```

## 3. Variáveis para cadastrar em `Var - F7`

- **DT1**
  - **Tipo**: Data
  - **Descrição**: Data Inicial Movimentação
  - **Valor Padrão**: (vazio / primeiro dia do período)
  - **Instrução**: Informe a data inicial da movimentação/operação financeira.

- **DT2**
  - **Tipo**: Data
  - **Descrição**: Data Final Movimentação
  - **Valor Padrão**: (vazio / data atual)
  - **Instrução**: Informe a data final da movimentação/operação financeira.

- **LT1**
  - **Tipo**: Literal
  - **Descrição**: Tipo Consulta (Espécies)
  - **Valor Padrão**: 0
  - **Instrução**: Informe as espécies separadas por vírgula (Ex: `ACRCOM, DEVREC`) ou `0` para consultar todas as espécies.

- **LT2**
  - **Tipo**: Literal
  - **Descrição**: Fornecedores
  - **Valor Padrão**: 0
  - **Instrução**: Informe o(s) código(s) de fornecedor separados por vírgula (Ex: `16474, 16491`) ou `0` para todos.

- **LT3**
  - **Tipo**: Literal
  - **Descrição**: Status (Aberto/Quitado)
  - **Valor Padrão**: A,Q
  - **Instrução**: Informe `A` para Aberto, `Q` para Quitado, `A,Q` para ambos ou `0` para ignorar.

- **LT4**
  - **Tipo**: Literal
  - **Descrição**: Usuários da Operação
  - **Valor Padrão**: 0
  - **Instrução**: Digite os logins de usuários separados por vírgula (Ex: `veridi, debco`) ou `0` / `TODOS` para trazer todas as alterações de qualquer usuário.

- **NR1**
  - **Tipo**: Numérico
  - **Descrição**: Numero do Titulo
  - **Valor Padrão**: 0
  - **Instrução**: Informe o número específico do título que deseja localizar ou `0` para não filtrar.

- **LS1**
  - **Tipo**: Lista
  - **Descrição**: Seleção de Rede
  - **Valor Padrão**: (vazio)
  - **Instrução**: Selecione a Rede (`GE_REDE`) dos Fornecedores desejados, ou mantenha ` TODAS AS REDES`.

## 4. SQL das listas `LSx`

Para carregar a lista de Redes no **LS1**, cole o SQL abaixo no campo de instrução da variável de lista:

```sql
SELECT ' TODAS AS REDES' FROM DUAL
UNION
SELECT DESCRICAO FROM GE_REDE
```

## 5. Passo a Passo Curto de Configuração
1. Abra a tela de **Consulta Criação** no ERP Consinco.
2. Cole o **SQL Principal** no campo de instrução SQL.
3. Clique no botão **Var - F7** para cadastrar os filtros da tela.
4. Cadastre `DT1` (Data) e `DT2` (Data) para as datas de movimentação.
5. Cadastre `LT1` (Literal) para Espécies.
6. Cadastre `LT2` (Literal) para Fornecedores.
7. Cadastre `LT3` (Literal) para Status (Aberto/Quitado).
8. Cadastre `LT4` (Literal) para Usuários da Operação.
9. Cadastre `NR1` (Numérico) para Número do Título.
10. Cadastre `LS1` (Lista) para Rede e cole o SQL da lista acima no campo de instrução.
11. Salve (`F4`), preencha os parâmetros e execute (`F8`).
