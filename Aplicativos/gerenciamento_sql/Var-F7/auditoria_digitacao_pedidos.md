# Filtros: Auditoria de Digitação de Pedidos

## Objetivo
Identificar logins que digitam pedidos no sistema, cruzando com dados de produto, quantidades, estoque no CD selecionado e data/hora. Permite expurgar dinamicamente usuários específicos do relatório (ex: robôs ou sistema automático).

## Variáveis Var - F7

| Variável | Tipo     | Descrição                | Valor Padrão | Instrução                                                                 |
|----------|----------|--------------------------|--------------|-------------------------------------------------------------------------|
| DT1      | Data     | Data Início Digitação    | -            | Informe a data inicial de busca.                                        |
| DT2      | Data     | Data Fim Digitação       | -            | Informe a data final de busca.                                          |
| NR1      | Numérico | Código do Produto        | 0            | Informe um SEQPRODUTO específico, ou deixe 0 para buscar todos.           |
| LT1      | Literal  | Empresas (Múltiplas)     | 0            | Digite o número da empresa que fez o pedido (ex: 1) ou separadas por vírgula (ex: 1, 2). Deixe 0 para todas. |
| NR2      | Numérico | Empresa do CD            | 0            | Informe o número da empresa do CD (ex: 1). Isso filtrará os pedidos direcionados a este CD e trará o estoque físico dele. Deixe 0 para não filtrar. |
| LT2      | Literal  | Expurgo de Usuários      | AUTOMATICO   | Digite os logins que não devem aparecer, separados por vírgula (ex: AUTOMATICO, joao, maria). Não importa se é maiúsculo ou minúsculo. Deixe 0 para não expurgar ninguém. |

## SQL Listas
*Não há variáveis LSx nesta consulta.*

## SQL Principal
Ver arquivo original gerado com as regras aplicadas.
