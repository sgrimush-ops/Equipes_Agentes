# Var-F7 - Confronto de Ativos CD 15 e CD 16

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/confronto_ativos_cd15_cd16.sql`

## Objetivo
Identificar e listar produtos que estão com status de compra ativo (`STATUSCOMPRA = 'A'`) simultaneamente no **CD 15** e no **CD 16**, permitindo a correção do CD fornecedor único. Apresenta o comprador responsável, o saldo de estoque disponível real de ambos os CDs, expurga categorias internas como `ALMOXARIFADO` e expurga as seções de perecíveis (`Frutas E Verduras`, `Padaria Baklizi` e `Padaria/Padadia Industrial`).

## Colunas Retornadas
- `COMPRADOR`: Nome do comprador responsável (`MAX_COMPRADOR`).
- `DEPARTAMENTO`: Descrição do departamento (Nível 1 da hierarquia).
- `CODIGO_PRODUTO`: Código interno do produto (`SEQPRODUTO`).
- `DESCRICAO`: Descrição completa do produto.
- `ESTOQUE_CD15`: Estoque físico disponível no CD 15 (Loja + Depósito - Reservas).
- `ESTOQUE_CD16`: Estoque físico disponível no CD 16 (Loja + Depósito - Reservas).
- `STATUS_CD15`: Status de compra no CD 15 (`A`).
- `STATUS_CD16`: Status de compra no CD 16 (`A`).

## Variáveis para Cadastrar em Var - F7

### LS1
- **Tipo**: Lista
- **Descrição**: Departamento
- **Valor padrão**: `0 - TODOS`
- **Instrução**: Selecione o departamento desejado ou deixe `0 - TODOS`.

## SQL da Lista LS1 (Total: 140 caracteres, respeitando o limite <= 145)
```sql
SELECT '0 - TODOS' FROM DUAL UNION SELECT CATEGORIA FROM MAP_CATEGORIA WHERE NIVELHIERARQUIA=1 AND STATUSCATEGOR='A' AND CATEGORIA!='ALMOXARIFADO'
```

## Passo a Passo para Configurar no Consinco (Consulta Criação)
1. Abra a tela de **Consulta Criação** no Totvs Consinco.
2. Cole o conteúdo de [confronto_ativos_cd15_cd16.sql](../querys/confronto_ativos_cd15_cd16.sql) na tela.
3. Pressione a tecla **F7** (ou clique no botão **Var - F7**).
4. Na aba **Lista**, cadastre a variável `LS1`:
   - **Nome**: `LS1`
   - **Descrição**: `Departamento`
   - **Valor Padrão**: `0 - TODOS`
   - **Retorno**: `Literal`
   - **SQL da Lista**: Cole a instrução SQL de linha única acima (140 caracteres).
5. Salve e execute a consulta com **F8**.
