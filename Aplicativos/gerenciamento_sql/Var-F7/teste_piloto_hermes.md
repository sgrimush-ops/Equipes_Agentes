# Var-F7 - teste_piloto_hermes

## Query Vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/teste_piloto_hermes.sql`

## Objetivo
Consulta de teste piloto gerada automaticamente a partir da fila de orquestração do Hermes Agent, validando a integração entre os agentes para o ERP TOTVS Consinco. Retorna o estoque por loja com filtros antes do Run.

## Variáveis para Cadastrar em Var - F7

### LT1
- **Tipo**: Literal
- **Descrição**: Código da(s) Loja(s)
- **Valor padrão**: 1,2,3,4,5,6,7,8,11,12,13,14,15,17,18
- **Instrução p/ o usuário**: Informe uma ou mais empresas separadas por vírgula (ou deixe vazio para todas as lojas da rede).

### NR1
- **Tipo**: Numérico
- **Descrição**: Estoque Mínimo
- **Valor padrão**: 1
- **Instrução p/ o usuário**: Informe o estoque total mínimo desejado para o filtro.
