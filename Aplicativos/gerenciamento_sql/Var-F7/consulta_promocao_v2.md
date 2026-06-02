# Var-F7 - consulta_promocao_v2

## Query vinculada
- Arquivo SQL: [Aplicativos/gerenciamento_sql/querys/consulta_promocao_v2.sql](../querys/consulta_promocao_v2.sql)

## Objetivo
Listar as promos por loja individual, sem consolidar empresas, com quantidade anterior, quantidade atual e valor total vendido calculado pelo mesmo metodo validado na investigacao.

## Colunas retornadas
- `PROMOCAO`: identificador da promocao.
- `DTAINICIO`: data inicial da promocao.
- `DTAFIM`: data final da promocao.
- `LOJA`: empresa individual da linha.
- `NOME`: sequencia da promocao.
- `COD`: codigo do produto.
- `DESCRICAO`: descricao completa do produto.
- `PRECO`: preco normal formatado como moeda (`R$`).
- `MGNORMAL`: margem normal formatada.
- `PROMO`: preco promocional formatado como moeda (`R$`).
- `MGPROMOC`: margem promocional formatada.
- `QTD_ANTERIOR`: quantidade vendida no periodo anterior.
- `QTD_ATUAL`: quantidade vendida no periodo atual.
- `VALOR_TOTAL_VENDIDO`: valor financeiro formatado como moeda (`R$`), calculado por preco promocional multiplicado pela quantidade vendida atual.

## Variaveis para cadastrar em Var - F7

### LT1
- Tipo: Literal
- Descricao: Lojas
- Instrucao: informe as lojas separadas por virgula (ex: 1,2,3,4).

### LS1
- Tipo: Lista
- Descricao: Oferta
- Instrucao: selecione a oferta no dropdown.

### DT1
- Tipo: Data
- Descricao: Data Inicial Periodo Anterior
- Instrucao: informe o inicio do periodo anterior.

### DT2
- Tipo: Data
- Descricao: Data Final Periodo Anterior
- Instrucao: informe o fim do periodo anterior.

### DT3
- Tipo: Data
- Descricao: Data Inicial Periodo Atual
- Instrucao: informe o inicio do periodo atual.

### DT4
- Tipo: Data
- Descricao: Data Final Periodo Atual
- Instrucao: informe o fim do periodo atual.

## SQL da lista LS1
- Tipo de retorno esperado: codigo da promocao (numerico), compativel com `M.PROMOCAO = :LS1`.
- SQL sugerida da lista:

```sql
SELECT DISTINCT
	P.PROMOCAO AS ITEM
FROM MRLV_BASEPRODPROMOC P
WHERE P.CENTRALLOJA = 'C'
	AND P.PRINCIPAL = 'S'
ORDER BY 1
```

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar LT1, LS1, DT1, DT2, DT3 e DT4 conforme os campos acima.
4. Salvar as variaveis.
5. Executar a consulta.

## Observacoes
- Esta versao mantem uma linha por empresa, sem somar lojas.
- A coluna `VALOR_TOTAL_VENDIDO` usa o mesmo metodo validado na investigacao: preco promocional da propria linha multiplicado pela quantidade atual da mesma loja.
- As quantidades anterior e atual sao obtidas por subconsultas agregadas em `LEFT JOIN` por produto e empresa, formato mais estavel para o parser da Consulta Criacao.
- Esta e a versao final consolidada para uso com filtros do usuario.
- O filtro de promocao usa comparacao direta `M.PROMOCAO = :LS1`.