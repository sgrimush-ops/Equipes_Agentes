# Var-F7 - consulta_mix_codigo_sw_unitario_com_custo

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_mix_codigo_sw_unitario_com_custo.sql`

## Objetivo
Igual a `consulta_mix_codigo_sw_unitario`, mas inclui tambem o custo liquido do produto (`CMULTCUSLIQUIDOEMP`) por loja. Permite consultar todas as lojas digitando 0 no filtro de loja.

## Variaveis para cadastrar em Var - F7

### NR1
- Tipo: Numerico
- Descricao: Codigo do produto
- Valor padrao: 0
- Instrucao ao usuario: Informe o codigo interno do produto no Consinco

### NR2
- Tipo: Numerico
- Descricao: Loja (0 = todas)
- Valor padrao: 0
- Instrucao ao usuario: Informe o numero da loja ou 0 para trazer todas as lojas

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar NR1 na aba Numerica com descricao "Codigo do produto" e valor padrao 0.
4. Cadastrar NR2 na aba Numerica com descricao "Loja (0 = todas)" e valor padrao 0.
5. Salvar as variaveis.
6. Fechar e reabrir a consulta.
7. Informar o codigo do produto em NR1.
8. Informar a loja em NR2 ou deixar 0 para trazer todas.
9. Executar a consulta.

## Observacoes
- Digitando 0 em NR2 a consulta ignora o filtro de loja e retorna o produto em todas as empresas cadastradas.
- O campo CUSTO_LIQUIDO vem de MRL_PRODUTOEMPRESA.CMULTCUSLIQUIDOEMP, que e o custo por loja.
- A consulta nao filtra por STATUSCOMPRA, entao itens inativos tambem aparecem.
- Os departamentos excluidos continuam sendo: A CLASSIFICAR, ALMOXARIFADO, INATIVAR e SERVICOS.
- Se o produto nao tiver codigo de transicao elegivel em MAP_PRODCODIGO, usa SEQPRODUTOBASEANTIGO como fallback.
