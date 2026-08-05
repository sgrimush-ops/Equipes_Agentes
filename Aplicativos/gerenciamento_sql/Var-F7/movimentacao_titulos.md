# movimentacao_titulos

## 1. Objetivo da Consulta
Fornecer um relatório de movimentação de títulos a pagar/receber (FI_TITULO), permitindo filtragem performática por período de vencimento, tipo de título, múltiplos fornecedores simultâneos e número de título específico.

## 2. SQL Principal
```sql
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
    (SELECT MAX(O.USUALTERACAO) KEEP (DENSE_RANK LAST ORDER BY NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO), O.SEQTITOPERACAO) 
       FROM FI_TITOPERACAO O WHERE O.SEQTITULO = T.SEQTITULO) AS USU_ULT_OPERACAO,
    (SELECT TO_CHAR(MAX(NVL(O.DTAHORAALTERACAO, O.DTAALTERACAO)), 'DD/MM/YYYY HH24:MI:SS') 
       FROM FI_TITOPERACAO O WHERE O.SEQTITULO = T.SEQTITULO) AS DTA_ULT_OPERACAO
FROM FI_TITULO T
LEFT JOIN GE_PESSOA P ON T.SEQPESSOA = P.SEQPESSOA
WHERE T.DTAVENCIMENTO BETWEEN :DT1 AND :DT2
  AND (:LT1 = '0' OR T.CODESPECIE IN (
      SELECT UPPER(TRIM(REGEXP_SUBSTR(:LT1, '[^,]+', 1, LEVEL)))
      FROM DUAL
      CONNECT BY REGEXP_SUBSTR(:LT1, '[^,]+', 1, LEVEL) IS NOT NULL
  ))
  AND (:NR1 = 0 OR T.NROTITULO = :NR1)
  AND (:LT2 = '0' OR T.SEQPESSOA IN (
      SELECT TO_NUMBER(REGEXP_SUBSTR(:LT2, '[^,]+', 1, LEVEL))
      FROM DUAL
      CONNECT BY REGEXP_SUBSTR(:LT2, '[^,]+', 1, LEVEL) IS NOT NULL
  ))
  AND (:LS1 = ' TODAS AS REDES' OR EXISTS (
      SELECT 1 FROM GE_REDEPESSOA RP
      JOIN GE_REDE R ON RP.SEQREDE = R.SEQREDE
      WHERE RP.SEQPESSOA = T.SEQPESSOA
        AND R.DESCRICAO = :LS1
  ))
  AND (:LT3 = '0' OR T.ABERTOQUITADO IN (
      SELECT UPPER(TRIM(REGEXP_SUBSTR(:LT3, '[^,]+', 1, LEVEL)))
      FROM DUAL
      CONNECT BY REGEXP_SUBSTR(:LT3, '[^,]+', 1, LEVEL) IS NOT NULL
  ))
ORDER BY T.DTAVENCIMENTO DESC, T.SEQPESSOA
```

## 3. Variáveis para cadastrar em `Var - F7`

- **LT1**
  - **Tipo**: Literal
  - **Descrição**: Tipo Consulta (Espécies)
  - **Valor Padrão**: 0
  - **Instrução**: Informe as espécies separadas por vírgula (Ex: ACRCOM, DEVREC) ou 0 para consultar todos. Não é *case-sensitive*.

- **LT2**
  - **Tipo**: Literal
  - **Descrição**: Fornecedores
  - **Valor Padrão**: 0
  - **Instrução**: Informe o(s) código(s) de fornecedor separados por vírgula (Ex: 16474, 16491) ou 0 para todos.

- **LT3**
  - **Tipo**: Literal
  - **Descrição**: Status (Aberto/Quitado)
  - **Valor Padrão**: A,Q
  - **Instrução**: Informe o status desejado separado por vírgula (Ex: A para Aberto, Q para Quitado, ou A,Q para ambos) ou 0 para ignorar.

- **NR1**
  - **Tipo**: Numérico
  - **Descrição**: Numero do Titulo
  - **Valor Padrão**: 0
  - **Instrução**: Informe o número específico do título que deseja localizar ou 0 para não filtrar.

- **DT1**
  - **Tipo**: Data
  - **Descrição**: Data Inicial
  - **Valor Padrão**: (vazio)
  - **Instrução**: Informe a data de início do filtro de vencimento.

- **DT2**
  - **Tipo**: Data
  - **Descrição**: Data Final
  - **Valor Padrão**: (vazio)
  - **Instrução**: Informe a data final do filtro de vencimento.

- **LS1**
  - **Tipo**: Lista
  - **Descrição**: Seleção de Rede
  - **Valor Padrão**: (vazio)
  - **Instrução**: Selecione a Rede (GE_REDE) dos Fornecedores desejados, ou mantenha " TODAS AS REDES".

## 4. SQL das listas `LSx`

Para carregar a lista de Redes no **LS1**, cole exatamente o SQL abaixo na janela de código da variável:

```sql
SELECT ' TODAS AS REDES' FROM DUAL
UNION
SELECT DESCRICAO FROM GE_REDE
```
*(Nota: O espaço no início de " TODAS AS REDES" garante que a opção fique sempre no topo quando a lista for ordenada alfabeticamente. Não adicione a palavra UNION sobrando no final, pois o Consinco fará o ORDER BY 1 automático).*

## 5. Passo a Passo Curto de Configuração
1. Abra a tela de `Consulta Criação`.
2. Cole o **SQL Principal** no campo de instrução SQL.
3. Clique no botão **Var - F7** para cadastrar os filtros da tela.
4. Cadastre `LT1` (Literal) para Tipo Consulta.
5. Cadastre `LT2` (Literal) para Fornecedores.
6. Cadastre `LT3` (Literal) para Status (Aberto/Quitado).
7. Cadastre `NR1` (Numérico) para Número do Título.
8. Cadastre `DT1` (Data) e `DT2` (Data) para as datas.
9. Cadastre `LS1` (Lista) para Rede e cole o SQL acima no campo de instrução dela.
10. Salve (`F4`), informe os filtros em tela e execute (`F8`).
