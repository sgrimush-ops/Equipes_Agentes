# Var-F7 - consulta_min_max_base

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_min_max_base.sql`

## Objetivo
Permitir escolher quantos dias de venda devem ser considerados do dia de ontem para tras.

## Variaveis para cadastrar em Var - F7

### NR1
- Tipo: Numerico
- Descricao: Dias de venda (ontem para tras)
- Valor padrao: 30
- Regra aplicada no SQL:
  - Data inicial: `TRUNC(SYSDATE) - NVL(:NR1, 30)`
  - Data final: menor que `TRUNC(SYSDATE)`
- Exemplo:
  - `NR1 = 1` considera somente ontem
  - `NR1 = 7` considera os ultimos 7 dias ate ontem

## Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar `NR1` na aba Numerico com descricao Dias de venda (ontem para tras).
4. Definir valor padrao `30`.
5. Salvar as variaveis.
6. Executar a consulta.

## Observacao importante
Os filtros visuais antes do Run nao nascem apenas do SQL; eles dependem do cadastro das variaveis na tela Var - F7.
