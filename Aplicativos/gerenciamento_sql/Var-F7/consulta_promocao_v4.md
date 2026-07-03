# Var-F7 - consulta_promocao_v4

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_promocao_v4.sql](../querys/consulta_promocao_v4.sql)

## Objetivo
Listar produtos em promocao com preco normal, preco promocional, quantidade vendida no periodo atual, quantidade vendida no periodo anterior, comprador da familia e uma coluna calculada de valor total vendido, com formatação garantindo o zero à esquerda nos decimais (ex: 0,00).

## Colunas retornadas
- `PROMOCAO`: identificador da promocao.
- `DTAINICIO`: data inicial da promocao.
- `DTAFIM`: data final da promocao.
- `COMPRADOR`: apelido (ou nome) do comprador vinculado à família (NRODIVISAO = 1).
- `NOME`: sequencia da promocao.
- `COD`: codigo do produto.
- `DESCRICAO`: descricao completa do produto.
- `PRECO`: preco normal (formatado com `FM999G990D00`).
- `MGNORMAL`: margem normal formatada (`FM999G990D99`).
- `PROMO`: preco promocional (formatado com `FM999G990D00`).
- `MGPROMOC`: margem promocional formatada (`FM999G990D99`).
- `QTD_ATUAL`: quantidade vendida no periodo atual.
- `QTD_ANTERIOR`: quantidade vendida no periodo anterior.
- `VALOR_TOTAL_VENDIDO`: preco promocional multiplicado pela quantidade vendida atual (formatado com `FM999G990D00` para evitar o efeito `,00`).

## Variaveis para cadastrar em Var - F7
Essa consulta usa as seguintes variaveis na tela de Consulta Criacao:

### LS1
- Tipo: Lista
- Descricao: Promocao
- Instrucao: selecione a promocao para filtrar a base principal e as subconsultas de vendas.

### LS2
- Tipo: Lista
- Descricao: Comprador
- Instrucao: selecione o comprador para filtrar ou mantenha `0 - TODOS` para trazer todos os compradores.

### DT1
- Tipo: Data
- Descricao: Data Inicial Periodo Anterior
- Instrucao: informe o inicio do periodo comparativo anterior.

### DT2
- Tipo: Data
- Descricao: Data Final Periodo Anterior
- Instrucao: informe o fim do periodo comparativo anterior.

### DT3
- Tipo: Data
- Descricao: Data Inicial Periodo Atual
- Instrucao: informe o inicio do periodo atual.

### DT4
- Tipo: Data
- Descricao: Data Final Periodo Atual
- Instrucao: informe o fim do periodo atual.

## SQL da lista LS1
Colar no cadastro da variável LS1 (Promoção):
```sql
SELECT DISTINCT PROMOCAO AS ITEM
FROM MRLV_BASEPRODPROMOC
WHERE CENTRALLOJA = 'C'
  AND PRINCIPAL = 'S'
ORDER BY 1
```

## SQL da lista LS2
Colar no cadastro da variável LS2 (Comprador - versão sem aspas literais para evitar ORA-01722):
```sql
SELECT '0 - TODOS' AS COMPRADOR
FROM DUAL
UNION
SELECT DISTINCT TO_CHAR(SEQCOMPRADOR) || ' - ' || NVL(APELIDO, COMPRADOR)
FROM MAX_COMPRADOR
WHERE STATUS = 'A'
ORDER BY 1
```

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao e colar o SQL atualizado.
2. Clicar em Var - F7.
3. Conferir o cadastro de LS1 como lista de promocao.
4. Cadastrar LS2 como lista de comprador.
5. Conferir os cadastros de DT1, DT2, DT3 e DT4 como datas.
6. Salvar as variaveis.
7. Executar a consulta.

## Observacoes
- A coluna `VALOR_TOTAL_VENDIDO` usa o preco promocional retornado e a quantidade agregada da subconsulta `Q1`.
- A formatação de todas as colunas de valor e margem foi ajustada para o modelo `FM999G990D00` / `FM999G990D99`, que garante a exibição do zero inteiro em valores como `0,00` em vez de `,00`.