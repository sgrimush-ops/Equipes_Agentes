# Var-F7 - relatorio_movimentacao_titulos_pagar

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/relatorio_movimentacao_titulos_pagar.sql`

## Objetivo
Replicação otimizada e performática do monitor de tela **Movimentação e Quitação de Títulos a Pagar (`FIMOVTITQUIT`)** do ERP Consinco. Permite analisar todas as operações financeiras (pagamentos, baixas, compensações, acréscimos e abatimentos) realizadas sobre os títulos de contas a pagar dentro de um período de vencimento.

## Evolução de Performance em relação ao Monitor Original
1. **Fim do Loop de Consultas (`FI_OPERACAO`):** No monitor original, o sistema executava uma query individual para buscar a descrição de cada código de operação (`SELECT DESCRICAO FROM FI_OPERACAO WHERE CODOPERACAO = X`). Nesta consulta otimizada, a tabela `FI_OPERACAO` é isolada em memória e unida via `LEFT JOIN`, trazendo o campo `DESCRICAO_OPERACAO` de uma única vez sem sobrecarregar o banco.
2. **CTEs Materializadas (`/*+ MATERIALIZE */`):** Isola na memória RAM do Oracle os dados das tabelas gigantes `FI_TITULO` e `FI_TITOPERACAO` antes dos cruzamentos.
3. **Bypass do Validador:** Envelopamento completo com `SELECT * FROM (` e código 100% livre de comentários para total compatibilidade com a Consulta Criação do Consinco.

## Colunas retornadas
- `EMPRESA`: Número da loja/empresa do título.
- `SEQ_TITULO`: Sequencial interno do título no ERP Consinco.
- `TITULO`: Número do título formatado (`NROTITULO/SERIE-PARCELA`).
- `ESPECIE`: Código da espécie do título (ex: DUPP, BONIAC, ALSCPC).
- `COD_FORNECEDOR`: Código sequencial do fornecedor (`SEQPESSOA`).
- `FORNECEDOR`: Nome ou Razão Social do fornecedor.
- `CNPJ_CPF`: CNPJ ou CPF formatado com máscara.
- `COD_OPERACAO`: Código numérico da operação realizada em `FI_TITOPERACAO`.
- `DESCRICAO_OPERACAO`: Descrição textual da operação bancária/financeira (ex: *Pagamento de Conta Corrente*, *Inclusão de Títulos*, *Taxa Recarga*).
- `DATA_OPERACAO`: Data em que a movimentação financeira ocorreu.
- `DATA_CONTABILIZA`: Data contábil do movimento.
- `DATA_EMISSAO`: Data de emissão da nota/título.
- `DATA_VENCIMENTO`: Data de vencimento do título.
- `DATA_PROGRAMADA`: Data programada para pagamento no banco.
- `DATA_QUITACAO`: Data de quitação final do título.
- `VALOR_OPERACAO`: Valor da operação bancária/financeira executada.
- `VALOR_NOMINAL_TITULO`: Valor original/nominal do título.
- `VALOR_PAGO_TITULO`: Valor acumulado já pago sobre o título.
- `SALDO_DEVEDOR_TITULO`: Saldo restante em aberto (`VLRNOMINAL - VLRPAGO`).
- `BANCO` / `AGENCIA` / `CONTA_CORRENTE`: Dados bancários e descrição da conta corrente utilizada.
- `USUARIO_ALTERACAO`: Usuário que realizou a operação no sistema.
- `OBSERVACAO_OPERACAO` / `OBSERVACAO_TITULO`: Histórico e observações do título e da operação.

## Variáveis para cadastrar em Var - F7

### DT1
- Tipo: Data
- Descrição: Data Inicial de Vencimento
- Instrução: informe a data inicial do período de vencimento dos títulos.

### DT2
- Tipo: Data
- Descrição: Data Final de Vencimento
- Instrução: informe a data final do período de vencimento dos títulos.

### NR1
- Tipo: Número
- Descrição: Filtro de Fornecedor ou Loja
- Valor padrão: 0
- Instrução: digite `0` para trazer todos os fornecedores/lojas ou informe um código específico para filtrar.

### LS1
- Tipo: Lista (com retorno Literal)
- Descrição: Filtro por Espécie de Documento (ex: DUPP)
- Valor padrão: 0 - TODOS
- Instrução: selecione `0 - TODOS` para trazer todas as espécies (inclusive boletos de serviço, frete, aluguel, etc.), ou escolha uma espécie específica como `DUPP`.

> [!CAUTION]
> **ATENÇÃO AO CADASTRAR A VARIÁVEL LS1 NO CONSINCO:**
> Não cole o código de filtro (`AND NVL(TRIM(:LS1)...`) dentro do cadastro da variável! O trecho `AND NVL...` já faz parte do arquivo principal da consulta. No campo **SQL da Lista** da variável `LS1`, cole **EXCLUSIVAMENTE** a query abaixo que busca as espécies na tabela `FI_ESPECIE`:

## SQL da lista LS1 (Para colar no campo de SQL da Lista da Variável LS1)
```sql
SELECT '0 - TODOS' AS CODESPECIE, '0 - TODOS' AS DESCRICAO FROM DUAL
UNION ALL
SELECT CODESPECIE, CODESPECIE || ' - ' || DESCRICAO AS DESCRICAO
FROM FI_ESPECIE
WHERE SITUACAO = 'A'
ORDER BY 1
```
