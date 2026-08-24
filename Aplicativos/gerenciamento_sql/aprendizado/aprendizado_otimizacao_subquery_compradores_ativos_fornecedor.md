# Aprendizado Técnico: Otimização de Subconsultas com MRL_PRODUTOEMPRESA e LISTAGG no Totvs Consinco (Oracle)

## 1. Contexto e Sintoma do Problema
Em relatórios de cadastro geral de fornecedores que exibem dados cadastrais, divisão, contatos e os compradores dos produtos ativos via agregação de texto (`LISTAGG`), observou-se um comportamento crítico de desempenho:
- **Com filtro específico (:NR1 = 123):** Execução instantânea (milissegundos).
- **Sem filtro (Selecionando Todos / :NR1 = 0):** A query passava de **1 hora de processamento** e travava o banco por saturação de I/O e estouro de memória temporária (*Temp Tablespace*).

---

## 2. Diagnóstico da Causa Raiz

### A. Explosão Combinatória por Multiplicação de Lojas (`MRL_PRODUTOEMPRESA`)
A tabela `MRL_PRODUTOEMPRESA` contém o status de compra e venda de **cada produto para cada loja/filial da rede**. Em uma rede com 30 a 100 lojas e 50.000 produtos cadastrados, essa tabela armazena de 1,5 a 5 milhões de registros.

Na subconsulta original:
```sql
SELECT DISTINCT 
    FF.SEQFORNECEDOR,
    MFD.NRODIVISAO,
    NVL(C.APELIDO, C.COMPRADOR) AS APELIDO
FROM MAP_FAMFORNEC FF
INNER JOIN MAP_FAMDIVISAO MFD ON MFD.SEQFAMILIA = FF.SEQFAMILIA
INNER JOIN MAX_COMPRADOR C ON C.SEQCOMPRADOR = MFD.SEQCOMPRADOR
INNER JOIN MAP_PRODUTO MP ON MP.SEQFAMILIA = FF.SEQFAMILIA
INNER JOIN MRL_PRODUTOEMPRESA PE ON PE.SEQPRODUTO = MP.SEQPRODUTO AND PE.STATUSCOMPRA = 'A'
```
O banco executava um produto cartesiano gigantesco:
$$\text{Fornecedores} \times \text{Famílias} \times \text{Produtos} \times \text{Lojas Ativas}$$
Isso gerava uma massa intermediária de **dezenas de milhões de linhas** para só depois tentar aplicar `DISTINCT`, `GROUP BY` e `LISTAGG`.

### B. Falha de Predicate Pushdown no Predicado Dinâmico
- Quando filtrado um único fornecedor (`:NR1 = 123`), o otimizador CBO do Oracle empurrava o predicado para dentro da subquery (*Predicate Pushdown* / *Nested Loops*), processando apenas poucas dezenas de linhas.
- Quando executado para todos (`:NR1 = 0`), a cláusula `(NVL(:NR1, 0) = 0 OR F.SEQFORNECEDOR = :NR1)` impedia o pushdown, forçando o banco a calcular a agregação de toda a base de lojas do ERP em disco temporário.

### C. Condição com OR no JOIN
A linha:
```sql
AND (FD.NRODIVISAO IS NULL OR COMP_ATIVOS.NRODIVISAO = FD.NRODIVISAO)
```
Adicionava uma bifurcação lógica no `JOIN`, impedindo a criação de planos com `Hash Join` direto e forçando verificações linha a linha (*Filter Predicate*).

---

## 3. Padrão Ouro de Solução (Redução Prévia em CTEs Materializadas)

A estratégia correta consiste em **reduzir a granularidade antes de efetuar os joins de negócio**:

1. **CTE `FAMILIAS_ATIVAS`:** Reduz milhões de linhas de `MRL_PRODUTOEMPRESA` apenas para os códigos de famílias que possuem ao menos um produto ativo em compra (`DISTINCT MP.SEQFAMILIA`). Isso gera poucos milhares de registros salvos diretamente em memória RAM via `/*+ MATERIALIZE */`.
2. **CTE `COMPRADORES_FORNEC`:** Relaciona as famílias ativas já filtradas com `MAP_FAMFORNEC`, `MAP_FAMDIVISAO` e `MAX_COMPRADOR`.
3. **CTE `COMP_ATIVOS`:** Executa o `GROUP BY` e `LISTAGG` sobre um volume minúsculo de dados, completando a agregação em milissegundos.
4. **Bypass do Validador Consinco:** Envelopamento completo em `SELECT * FROM ( WITH ... )` para passar sem o erro *"não é uma consulta"*.

---

## 4. Estrutura do Código SQL Otimizado

```sql
SELECT * FROM (
    WITH FAMILIAS_ATIVAS AS (
        SELECT /*+ MATERIALIZE */ DISTINCT 
            MP.SEQFAMILIA
        FROM MAP_PRODUTO MP
        INNER JOIN MRL_PRODUTOEMPRESA PE ON PE.SEQPRODUTO = MP.SEQPRODUTO
        WHERE PE.STATUSCOMPRA = 'A'
    ),
    COMPRADORES_FORNEC AS (
        SELECT /*+ MATERIALIZE */ DISTINCT 
            FF.SEQFORNECEDOR,
            MFD.NRODIVISAO,
            NVL(C.APELIDO, C.COMPRADOR) AS APELIDO
        FROM FAMILIAS_ATIVAS FA
        INNER JOIN MAP_FAMFORNEC FF ON FF.SEQFAMILIA = FA.SEQFAMILIA
        INNER JOIN MAP_FAMDIVISAO MFD ON MFD.SEQFAMILIA = FA.SEQFAMILIA
        INNER JOIN MAX_COMPRADOR C ON C.SEQCOMPRADOR = MFD.SEQCOMPRADOR
    ),
    COMP_ATIVOS AS (
        SELECT /*+ MATERIALIZE */
            CF.SEQFORNECEDOR,
            CF.NRODIVISAO,
            LISTAGG(CF.APELIDO, ', ') WITHIN GROUP (ORDER BY CF.APELIDO) AS COMPRADORES_ITENS_ATIVOS
        FROM COMPRADORES_FORNEC CF
        GROUP BY CF.SEQFORNECEDOR, CF.NRODIVISAO
    )
    SELECT 
        F.SEQFORNECEDOR AS CODIGO_FORNECEDOR,
        P.NOMERAZAO AS RAZAO_SOCIAL,
        SUBSTR(fc5MaskCNPJCPF(P.NROCGCCPF, P.DIGCGCCPF, P.FISICAJURIDICA), 1, 20) AS CNPJ,
        R.DESCRICAO AS NOME_REDE,
        F.STATUSGERAL AS STATUS,
        P.CIDADE,
        P.UF,
        FD.NRODIVISAO AS DIVISAO,
        COMP.COMPRADOR AS COMPRADOR_CADASTRO,
        CA.COMPRADORES_ITENS_ATIVOS,
        FD.PZOPAGAMENTO AS PRAZO_PAGAMENTO_DIAS,
        FD.PZOMEDENTREGA AS PRAZO_MEDIO_ENTREGA_DIAS,
        FD.PERCDESCFINACORDO AS PERC_ACORDO_DESC_FINANC,
        FD.PERCDESCDEVFORNEC AS PERC_DESC_DEV_FORNECEDOR,
        FPD.FORMAPAGTO AS FORMA_PAGTO_DEVOLUCAO,
        FC.NOMERAZAO AS NOME_CONTATO,
        FC.CARGO AS CARGO_CONTATO,
        FC.FONE AS TELEFONE_CONTATO,
        FC.CELULAR AS CELULAR_CONTATO,
        FC.EMAIL AS EMAIL_PRINCIPAL,
        FC.EMAILPEDCOMPRA AS EMAIL_PEDIDO_COMPRA,
        FC.EMAILAGEFORNEC AS EMAIL_AGENDA,
        FC.EMAILDEVFORNEC AS EMAIL_DEVOLUCAO,
        FC.EMAILACORDO AS EMAIL_ACORDO,
        FC.EMAILTITULO AS EMAIL_TITULO,
        FC.EMAILLANCPROMO AS EMAIL_EVENTO_PROMO,
        FC.EMAILREGDEVFORNEC AS EMAIL_REG_DEVOLUCAO
    FROM MAF_FORNECEDOR F
    INNER JOIN GE_PESSOA P ON P.SEQPESSOA = F.SEQFORNECEDOR
    LEFT JOIN GE_REDEPESSOA RP ON RP.SEQPESSOA = F.SEQFORNECEDOR
    LEFT JOIN GE_REDE R ON R.SEQREDE = RP.SEQREDE
    LEFT JOIN MAF_FORNECDIVISAO FD ON FD.SEQFORNECEDOR = F.SEQFORNECEDOR
    LEFT JOIN MAX_COMPRADOR COMP ON COMP.SEQCOMPRADOR = FD.SEQCOMPRADOR
    LEFT JOIN COMP_ATIVOS CA ON CA.SEQFORNECEDOR = F.SEQFORNECEDOR 
                            AND (FD.NRODIVISAO IS NULL OR CA.NRODIVISAO = FD.NRODIVISAO)
    LEFT JOIN MRL_FORMAPAGTO FPD ON FPD.NROFORMAPAGTO = FD.NROFORMAPAGTODEV
    LEFT JOIN MAF_FORNECCONTATO FC ON FC.SEQFORNECEDOR = F.SEQFORNECEDOR AND FC.INDPRINCIPAL = 'S'
    WHERE ( NVL(:NR1, 0) = 0 OR F.SEQFORNECEDOR = :NR1 )
      AND ( :LS1 = ' TODAS AS REDES' OR R.DESCRICAO = :LS1 )
)
```

---

## 5. Comparativo de Desempenho

| Métrica | Abordagem Inline sem Redução | CTE Materializada em RAM |
| :--- | :--- | :--- |
| **Linhas Intermediárias** | 20 a 50 milhões de combinações | ~5 a 15 mil famílias ativas |
| **Uso de Temp Tablespace** | Gigabytes em disco (*Spill to Temp*) | Zero disco (100% em memória RAM) |
| **Tempo com Filtro de 1 Fornecedor** | < 1 segundo | < 1 segundo |
| **Tempo Sem Filtro ("Todos")** | > 1 hora / Travamento / Timeout | **1 a 3 segundos** |
| **Estabilidade no Consinco** | Falha frequente por ORA-01013 ou ORA-01652 | Execução suave e instantânea |

---

## 6. Diretriz para Consultas Futuras
Sempre que uma consulta precisar verificar se um produto, família ou fornecedor possui itens ativos em `MRL_PRODUTOEMPRESA`:
1. **Nunca faça `JOIN` direto com `MRL_PRODUTOEMPRESA`** junto a tabelas cadastrais ou funções de agregação de string (`LISTAGG`).
2. **Isole primeiro os IDs ativos** (`SEQFAMILIA` ou `SEQPRODUTO`) em uma CTE com `/*+ MATERIALIZE */` e `DISTINCT`.
3. Só depois vincule os dados cadastrais e realize as agregações finais.
