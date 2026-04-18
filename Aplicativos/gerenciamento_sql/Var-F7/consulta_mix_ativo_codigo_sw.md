# Var-F7 - consulta_mix_ativo_codigo_sw

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_mix_ativo_codigo_sw.sql`

## Objetivo
Consulta para listar o mix ativo da loja informada antes do Run, exibindo:
- departamento
- codigo do produto
- descricao do produto
- status de compra
- codigo de transicao

O codigo de transicao foi tratado com prioridade para a `MAP_PRODCODIGO`, usando o `CODACESSO` do `TIPCODIGO = 'I'`, que foi o padrao evidenciado na investigacao do produto 10 para a linha exibida como Transicao na tela MAX0091. Quando houver mais de um registro elegivel, a consulta prioriza embalagem `1`. Se nao houver registro `I`, a consulta ainda tenta aproveitar linhas com datas de utilizacao de codigo de transicao e, por ultimo, usa `MAP_PRODUTO.SEQPRODUTOBASEANTIGO` como fallback.

## Variaveis para cadastrar em Var - F7

### LT1
- Tipo: Literal
- Descricao: Loja
- Valor padrao: 1
- Instrucao p/ o usuario: Informe uma ou mais lojas separadas por virgula, por exemplo 1 ou 1,3,15

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Excluir a variavel LS1 antiga, se ela ainda existir nessa consulta.
4. Cadastrar LT1 na aba Literal.
5. Definir a descricao como Loja.
6. Definir o valor padrao como 1.
7. Salvar as variaveis.
8. Fechar e reabrir a consulta.
9. Voltar para a consulta, informar a loja e executar.

## Observacoes
- Os filtros visuais antes do Run nao nascem apenas do SQL; eles dependem do cadastro da variavel em Var - F7.
- Neste caso foi usado `LT1` em vez de `LS1` porque a lista nao liberou o Run na tela e o literal e o caminho mais estavel neste ambiente.
- Se a consulta continuar mostrando dropdown de lista, isso indica que a `LS1` antiga ainda esta cadastrada na tela dessa consulta e precisa ser removida manualmente no Var - F7.
- A consulta considera mix ativo pelo criterio `STATUSCOMPRA = 'A'` na `MRL_PRODUTOEMPRESA`.
- Os departamentos fantasmas excluidos sao `A CLASSIFICAR`, `ALMOXARIFADO`, `INATIVAR` e `SERVICOS`.
- A consulta nao usa mais a heuristica por fornecedor; a prioridade agora parte diretamente do `TIPCODIGO = 'I'`, conforme a evidencia levantada na base.
- Se um produto nao possuir codigo de transicao em `MAP_PRODCODIGO`, a consulta tenta usar `SEQPRODUTOBASEANTIGO` como fallback.
- Se a coluna continuar vazia mesmo assim, isso indica que a base nao possui codigo legado preenchido para aquele item.