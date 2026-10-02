# Aprendizado: Regra de Ouro da Pirâmide de Afunilamento e Pesquisa Inteligente Inicial

## 1. Princípio Fundamental (O Topo da Pirâmide)
Em bancos de dados corporativos de grande porte como o **Oracle / TOTVS Consinco**, tabelas de movimentação transacional e analítica (como `MRL_CUSTODIA`, `MLF_NOTAFISCAL`, `MLF_NFITEM`, `MRL_PRODUTOEMPRESA`) armazenam dezenas a centenas de milhões de registros de todas as filiais ao longo dos anos.

Quando um usuário ou relatório solicita a filtragem por **códigos específicos** (como `SEQFORNECEDOR`, `SEQPRODUTO`, `SEQCOMPRADOR`, `SEQCATEGORIA` ou `NROEMPRESA`), esses códigos **DEVEM SER O TOPO DA PIRÂMIDE**, isto é, o primeiro bloco executado na query.

```
       ▲  [ TOPO DA PIRÂMIDE: Filtro Inteligente Inicial ]
      / \   (Filtra Fornecedor/Produto/Comprador: 50 a 200 registros em RAM)
     /   \
    /=====\
   /       \  [ MEIO: Join Direcionado por Índice em Tabelas Pesadas ]
  /         \   (MRL_CUSTODIA / NOTAFISCAL buscando apenas os ~50 itens)
 /===========\
/             \  [ BASE DA PIRÂMIDE: Resultado Final Agregado em Milissegundos ]
```

---

## 2. O Anti-Padrão (Varredura Massiva / Full Scan) ❌
### O que causa travamento e timeout:
Tentar varrer a tabela analítica pesada para **todo o banco de dados** antes de saber quais produtos ou fornecedores serão analisados.

```sql
-- ANTI-PADRÃO: Varrer MRL_CUSTODIA inteira da rede nos últimos 90 dias
WITH CTE_PRODUTOS_VENDIDOS AS (
    SELECT /*+ MATERIALIZE */ DISTINCT
        C.SEQPRODUTO
    FROM MRL_CUSTODIA C
    WHERE C.DTAENTRADASAIDA >= TRUNC(SYSDATE) - 90
      AND NVL(C.QTDVDA, 0) > 0
)
-- O Oracle precisa ler dezenas de milhões de linhas da rede inteira e 
-- calcular DISTINCT de 50.000 produtos na memória RAM.
-- RESULTADO: TIMEOUT / SESSÃO TRAVADA.
```

---

## 3. O Padrão Correto (Pirâmide de Afunilamento Inicial) ✅
### Como estruturar para rodar em milissegundos:

1. **Passo 1 (Topo da Pirâmide):** Isolar os produtos/famílias pertencentes aos códigos informados (ex: fornecedores `17017, 8714`) em uma CTE materializada.
2. **Passo 2 (Join com Índice):** Cruzar a tabela pesada (`MRL_CUSTODIA`) fazendo `INNER JOIN` direto com a lista pequena do Passo 1. O Oracle aproveita os índices por `SEQPRODUTO` e `DTAENTRADASAIDA`, lendo apenas os blocos de dados estritamente necessários.
3. **Passo 3 (Resultado):** Filtrar o resultado final instantaneamente.

```sql
SELECT * FROM (
    WITH PRODUTOS_FORNEC AS (
        SELECT /*+ MATERIALIZE */
            A.SEQPRODUTO,
            A.DESCCOMPLETA,
            FF.SEQFORNECEDOR AS COD_FORNECEDOR,
            PES.NOMERAZAO AS RAZAO_FORNECEDOR,
            FF.PRINCIPAL AS FORN_PRINCIPAL,
            TO_CHAR(TRUNC(A.DTAHORINCLUSAO), 'DD/MM/YYYY') AS DATA_CADASTRO
        FROM MAP_PRODUTO A
        INNER JOIN MAP_FAMFORNEC FF 
            ON FF.SEQFAMILIA = A.SEQFAMILIA
        INNER JOIN GE_PESSOA PES 
            ON PES.SEQPESSOA = FF.SEQFORNECEDOR
        WHERE FF.SEQFORNECEDOR IN (17017, 8714)
          AND TRUNC(A.DTAHORINCLUSAO) <= TRUNC(SYSDATE) - 90
          AND EXISTS (
              SELECT 1 
              FROM MRL_PRODUTOEMPRESA PE 
              WHERE PE.SEQPRODUTO = A.SEQPRODUTO 
                AND PE.STATUSCOMPRA = 'A'
          )
    ),
    VENDAS_90D AS (
        SELECT /*+ MATERIALIZE */
            C.SEQPRODUTO,
            SUM(NVL(C.QTDVDA, 0)) AS TOTAL_QTD_VENDIDA
        FROM MRL_CUSTODIA C
        INNER JOIN PRODUTOS_FORNEC PF 
            ON PF.SEQPRODUTO = C.SEQPRODUTO
        WHERE C.DTAENTRADASAIDA >= TRUNC(SYSDATE) - 90
        GROUP BY C.SEQPRODUTO
    )
    SELECT DISTINCT
        PF.SEQPRODUTO,
        PF.DESCCOMPLETA,
        PF.COD_FORNECEDOR,
        PF.RAZAO_FORNECEDOR,
        PF.FORN_PRINCIPAL,
        PF.DATA_CADASTRO
    FROM PRODUTOS_FORNEC PF
    LEFT JOIN VENDAS_90D V 
        ON V.SEQPRODUTO = PF.SEQPRODUTO
    WHERE NVL(V.TOTAL_QTD_VENDIDA, 0) = 0
    ORDER BY 
        PF.COD_FORNECEDOR,
        PF.DESCCOMPLETA
)
```

---

## 4. Checklist para Novas Queries
- [ ] Foram informados códigos de Fornecedor, Produto, Comprador ou Categoria?
- [ ] O filtro desses códigos está no **primeiro bloco `WITH`** da query?
- [ ] A tabela pesada (`MRL_CUSTODIA` / `MLF_NOTAFISCAL` / `MLF_NFITEM`) está cruzando diretamente com os `SEQPRODUTO` afunilados?
- [ ] As CTEs utilizam o hint `/*+ MATERIALIZE */`?
- [ ] O código final não contém comentários `--` ou `/* */` que possam quebrar no SGI?
