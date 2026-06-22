# Aprendizado: Configurações Comerciais e Financeiras de Fornecedores (Consinco)

**Data da Descoberta**: Junho/2026
**Contexto**: Levantamento de dados de fornecedores (Prazo de Pagamento, Forma de Pagamento, Prazo de Entrega, Condições de Devolução). Inicialmente, houve a tentativa de inferir o prazo através do histórico do contas a pagar (`FI_TITULO`), porém, a tela oficial do ERP lê as parametrizações estáticas de negócio da tabela `MAF_FORNECDIVISAO`.

## Tabelas Chaves Mapeadas

### 1. `MAF_FORNECDIVISAO`
Diferente da tabela mestre `GE_PESSOA` (que contém apenas CNPJ, Razão Social, etc.) ou `MAF_FORNECEDOR` (que contém flags gerais), as regras de negócio de como a empresa compra daquele fornecedor ficam segmentadas por **Divisão** na tabela `MAF_FORNECDIVISAO`.

Principais colunas descobertas através do log nativo (Monitor) do Consinco:
- **`PZOPAGAMENTO` (VARCHAR2)**: Armazena o prazo exato cadastrado em tela (ex: `15`, `30/45/60`). 
- **`PZOMEDENTREGA` (NUMBER)**: Prazo médio de entrega em dias (ex: `10`).
- **`INDPZOPAGAMENTO` (VARCHAR2)**: Indicador da Forma de Pagamento. Para exibir o texto amigável da tela, deve-se usar um DECODE:
  - `'F'` = Faturamento
  - `'V'` = A Vista
  - `'A'` = Antecipado
  - `'C'` = Contra Apresentação
- **`NROFORMAPAGTODEV` (NUMBER)**: Chave estrangeira para a Forma de Pagamento de Devoluções.
- **`NROCONDPAGDEV` (NUMBER)**: Chave estrangeira para a Condição de Pagamento de Devoluções.
- **`TIPODTABASEVENCTO` (VARCHAR2)**: Tipo de data base para o vencimento (ex: `'E'` = Data de Emissão, `'R'` = Data de Recebimento).

### 2. Tabelas de Domínio de Pagamento
Para buscar as descrições literais (Forma de Devolução e Condição de Devolução), é necessário fazer JOINs (`LEFT JOIN`) com tabelas auxiliares:
- **`MRL_FORMAPAGTO`**: Mapeia `NROFORMAPAGTO` -> `FORMAPAGTO` (Descrição da Forma de Pagamento).
- **`MAD_CONDICAOPAGTO`**: Mapeia `NROCONDICAOPAGTO` -> `DESCCONDICAOPAGTO` (Descrição da Condição de Pagamento).

## Estrutura de Join Validada (Padrão Ouro)
Sempre que o usuário solicitar "Prazo de Pagamento Cadastrado" ou dados contratuais do fornecedor, **NÃO utilize inferências em `FI_TITULO`**. Utilize a arquitetura abaixo:

```sql
SELECT 
    G.SEQPESSOA AS CODIGO_FORNECEDOR,
    G.NOMERAZAO AS DESCRICAO_FORNECEDOR,
    C.COMPRADOR,
    MFD.PZOPAGAMENTO AS PRAZO_PAGAMENTO_CADASTRO,
    MFD.PZOMEDENTREGA AS PRAZO_MEDIO_ENTREGA_DIAS,
    DECODE(MFD.INDPZOPAGAMENTO, 
        'F', 'Faturamento', 
        'V', 'A Vista', 
        'A', 'Antecipado', 
        'C', 'Contra Apresentacao', 
        MFD.INDPZOPAGAMENTO) AS FORMA_PAGAMENTO,
    FPDEV.FORMAPAGTO AS FORMA_DEVOLUCAO,
    CPDEV.DESCCONDICAOPAGTO AS CONDICAO_DEVOLUCAO
FROM GE_PESSOA G
INNER JOIN MAP_FAMFORNEC FF 
    ON FF.SEQFORNECEDOR = G.SEQPESSOA
INNER JOIN MAP_FAMDIVISAO FD 
    ON FD.SEQFAMILIA = FF.SEQFAMILIA
INNER JOIN MAX_COMPRADOR C 
    ON C.SEQCOMPRADOR = FD.SEQCOMPRADOR
-- Join estratégico para regras comerciais de compra:
LEFT JOIN MAF_FORNECDIVISAO MFD 
    ON MFD.SEQFORNECEDOR = FF.SEQFORNECEDOR 
   AND MFD.NRODIVISAO = FD.NRODIVISAO
-- Joins de dominio financeiro:
LEFT JOIN MRL_FORMAPAGTO FPDEV 
    ON FPDEV.NROFORMAPAGTO = MFD.NROFORMAPAGTODEV
LEFT JOIN MAD_CONDICAOPAGTO CPDEV 
    ON CPDEV.NROCONDICAOPAGTO = MFD.NROCONDPAGDEV
```

## Regra de Ouro (Consulta Criação)
Sempre que uma Query for criada para ser embutida na tela "Consulta Criação" do Consinco:
1. A instrução DEVE obrigatoriamente iniciar com a palavra literal `SELECT`.
2. **NÃO utilize** a cláusula `WITH` (CTE) na raiz. Se for usar subqueries complexas, embuta como uma *Inline View* dentro do `FROM` ou de um `LEFT JOIN (...) ON (...)`.
3. Não insira comentários (`--` ou `/* */`) no código final, pois o validador sintático do Consinco é frágil e pode retornar a mensagem "A instrução SQL informada, não é uma consulta."
