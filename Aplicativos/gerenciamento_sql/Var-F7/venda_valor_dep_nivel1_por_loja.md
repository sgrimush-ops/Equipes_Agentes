# Var-F7 - venda_valor_dep_nivel1_por_loja

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/venda_valor_dep_nivel1_por_loja.sql`

## Objetivo
Consolidar as vendas em valores reais (VLRITEM das notas fiscais de saida) agrupadas por Departamento (nivel hierarquico 1) e Loja (NROEMPRESA) no periodo informado. Filtros: periodo e comprador.

## Colunas retornadas
- `DEPARTAMENTO`: categoria nivel 1 da familia do produto.
- `LOJA`: numero da empresa (NROEMPRESA).
- `VLR_VENDAS`: soma do valor do item nas notas fiscais de saida (VLRITEM) por departamento e loja no periodo.

## Fonte dos dados
A query usa MLFV_BASENFE + MFLV_BASEDFITEM (notas fiscais de saida, operacao 800), que e a fonte homologada para relatorios de venda por valor no workspace. Nao usa MRL_PRODVENDADIA porque essa tabela guarda quantidade e nao valor de venda.

## Variaveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descricao: Data Inicial Venda
- Instrucao: informe a data inicial do periodo de venda

### DT2
- Tipo: Data
- Descricao: Data Final Venda
- Instrucao: informe a data final do periodo de venda

### LS3
- Tipo: Lista
- Descricao: Comprador (gestor de categoria)
- Valor padrao: 0 - TODOS
- Instrucao: selecione o comprador na lista ou mantenha 0 - TODOS para nao filtrar

## SQL da lista LS3
```sql
SELECT '0 - TODOS' AS COMPRADOR FROM DUAL
UNION ALL
SELECT TO_CHAR(SEQCOMPRADOR) || ' - ' || APELIDO AS COMPRADOR
FROM MAX_COMPRADOR
WHERE STATUS = 'A'
ORDER BY 1
```

## Passo a passo operacional
1. Abrir ou criar a consulta na tela Consulta Criacao e colar o SQL do arquivo vinculado.
2. Clicar em Var - F7.
3. Cadastrar DT1 na aba Data com descricao Data Inicial Venda.
4. Cadastrar DT2 na aba Data com descricao Data Final Venda.
5. Cadastrar LS3 na aba Lista com descricao Comprador, colar a SQL da lista acima e definir valor padrao 0 - TODOS.
6. Salvar todas as variaveis.
7. Executar a consulta; os filtros aparecerao antes do Run.

## Observacoes
- Os filtros visuais nao nascem apenas do SQL; dependem do cadastro em Var - F7.
- Valor de venda extraido de MFLV_BASEDFITEM.VLRITEM (valor real da NF), nao calculado por quantidade x preco.
- Restrito a CODGERALOPER = 800 e TIPNOTAFISCAL = 'S' (operacoes de venda homologadas).
- Departamentos internos (A CLASSIFICAR, ALMOXARIFADO, INATIVAR, SERVICOS) sao excluidos pelo filtro de TIPCATEGORIA = 'M' e NOT IN na subquery de departamento.
- Escopo de lojas: 1 a 8, 11 a 15, 17 e 18 (inclui loja 15 conforme modelo Relatorio_Venda_Departamento homologado).
- O filtro de comprador usa o padrao homologado: lista no formato `codigo - apelido`, sentinela `0 - TODOS`, extracao do codigo via SUBSTR/INSTR para comparar com MAP_FAMDIVISAO.SEQCOMPRADOR.
