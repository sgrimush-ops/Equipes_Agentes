# Procedimento de Cadastro de Variáveis - Consulta Monitoramento Pessoa Jurídica

## 1. SQL principal
Arquivo: querys/consulta_monitoramento_pessoa_juridica.sql

## 2. Variáveis para Var-F7

- LT1: Tipo de Pessoa (Padrão: 'J')
  - Tipo: Lista de seleção
  - Opções: 'J' (Pessoa Jurídica), 'F' (Pessoa Física)
- LT2: Status
  - Tipo: Lista múltipla
  - SQL da lista (LS2):
    ```sql
    SELECT 'A' AS CODIGO, 'Ativo' AS DESCRICAO FROM DUAL
    UNION ALL
    SELECT 'I', 'Inativo' FROM DUAL
    UNION ALL
    SELECT 'P', 'Prospect' FROM DUAL
    ```
- LS1: Nome/Razão Social (Filtro textual, opcional)
  - Tipo: Texto livre
  - Dica: Deixe 'TODOS' para não filtrar

## 3. Passo a passo de cadastro
1. Cadastre a query principal em `querys/consulta_monitoramento_pessoa_juridica.sql`.
2. No Var-F7, cadastre as variáveis:
   - LT1 (Lista simples): 'J' (Pessoa Jurídica), 'F' (Pessoa Física)
   - LT2 (Lista múltipla, use SQL LS2 acima)
   - LS1 (Texto livre, padrão 'TODOS')
3. Relacione as variáveis conforme o SQL.
4. Teste a consulta na tela Consulta Criação, validando os filtros antes do Run.

## Observações
- Os filtros visuais dependem do cadastro correto das variáveis em Var-F7.
- Para grandes volumes, sempre selecione filtros antes de executar.
