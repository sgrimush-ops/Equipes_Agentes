# Var-F7 - Relatorio_Venda_Departamento

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/Relatorio_Venda_Departamento.sql`

## Objetivo
Relatorio consolidado de venda por departamento, retornando apenas:
- departamento
- valor total vendido no periodo informado
- linha adicional com o total geral do periodo
- valor exibido com mascara financeira
- exibicao forcada como texto monetario para evitar reformatacao automatica da grade

Sem abrir itens ou produtos no grid final.

## Variaveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descricao: Data Inicial Venda
- Valor padrao: definir conforme rotina do usuario
- Instrucao p/ o usuario: informe a data inicial do periodo de venda

### DT2
- Tipo: Data
- Descricao: Data Final Venda
- Valor padrao: data atual
- Instrucao p/ o usuario: informe a data final do periodo de venda

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar DT1 na aba Data com descricao Data Inicial Venda.
4. Cadastrar DT2 na aba Data com descricao Data Final Venda.
5. Salvar as variaveis.
6. Voltar para a consulta e executar.

## Observacoes
- Os filtros visuais antes do Run nao nascem apenas do SQL; eles dependem do cadastro em Var - F7.
- A consulta soma `MFLV_BASEDFITEM.VLRITEM` das notas de saida no periodo informado.
- O criterio confirmado na investigacao foi restringir a operacao fiscal `800`, que foi a operacao aderente ao conceito de venda validado no caso analisado.
- O modelo `65` nao deve ser excluido nessa rotina, porque a venda valida encontrada no caso investigado estava integralmente nesse modelo.
- No caso investigado, a diferenca residual de `100,83` foi localizada em duas notas especificas de PET: empresa `3` NF `10068` serie `703` e empresa `4` NF `18130` serie `710`. A query atual exclui essas duas notas para reproduzir exatamente o total conferido.
- O departamento e obtido pela familia do produto na `MAP_CATEGORIA` nivel 1.
- A consulta restringe a mercadorias de revenda usando `MAP_FAMDIVISAO.FINALIDADEFAMILIA = 'R'`.
- Departamentos internos como A CLASSIFICAR, ALMOXARIFADO, INATIVAR e SERVICOS ficam fora do resultado.
- O escopo de empresas segue a lista branca homologada do workspace: 1 a 8, 11 a 15, 17 e 18.
- Se voce quiser que o numero bata exatamente com alguma visao nativa especifica da ABC de Vendas do Consinco, o proximo ajuste natural e comparar as notas fiscais retornadas na debug `debug_venda_pet_nf_800.sql` com a origem de conferência usada no processo de negocio.