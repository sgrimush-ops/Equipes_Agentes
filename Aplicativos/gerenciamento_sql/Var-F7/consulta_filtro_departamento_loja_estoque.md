# Var-F7 - consulta_filtro_departamento_loja_estoque

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_filtro_departamento_loja_estoque.sql`

## Objetivo
Consulta de produtos por loja com filtros antes do Run para:
- empresa
- estoque maior que
- departamento

## Variaveis para cadastrar em Var - F7

### LT1
- Tipo: Literal
- Descricao: Nro Empresa
- Valor padrao: 1,2,3,4,5,6,7,8,11,12,13,14,15,17,18
- Instrucao p/ o usuario: Informe uma ou mais empresas separadas por virgula

### NR1
- Tipo: Numerico
- Descricao: Estoque Maior Que
- Valor padrao: 0
- Instrucao p/ o usuario: Informe o estoque minimo para filtrar

### LS1
- Tipo: Lista
- Descricao: Departamento
- Tipo de retorno: Literal
- Instrucao p/ o usuario: Selecione o departamento desejado
- Tipo IN: Desmarcado

## SQL da lista LS1
Cole esta SQL dentro da propria variavel LS1 na tela Var - F7:

```sql
SELECT DISTINCT
    A.CATEGORIA
FROM MAP_CATEGORIA A
WHERE A.STATUSCATEGOR = 'A'
  AND A.TIPCATEGORIA = 'M'
  AND A.NIVELHIERARQUIA = 1
ORDER BY A.CATEGORIA
```

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar LT1 na aba Literal com a descricao e valor padrao informados acima.
4. Cadastrar NR1 na aba Numerico com a descricao e valor padrao informados acima.
5. Cadastrar LS1 na aba Lista.
6. Definir LS1 com retorno Literal.
7. Colar a SQL da lista no quadro da variavel LS1.
8. Testar a lista dentro da propria tela da variavel antes de salvar.
9. Salvar as variaveis.
10. Voltar para a consulta e executar.

## Observacoes
- Os filtros visuais antes do Run nao nascem apenas do SQL; eles dependem do cadastro em Var - F7.
- Nesta consulta, o departamento e filtrado por texto em `MAP_CATEGORIA` nivel 1.
- Se uma nova query com filtros for criada, gerar um novo arquivo nesta pasta seguindo o mesmo padrao e preferencialmente com o mesmo nome-base da query SQL.