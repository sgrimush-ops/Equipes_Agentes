# Consulta Criação: consulta_produtos_ativos_fornecedor_emp15

## 1. Objetivo da Consulta
Listar todos os produtos com cadastro ativo para compra (`STATUSCOMPRA = 'A'`) na **Empresa 15 (CD 15)** vinculados a um determinado fornecedor informado via parâmetro (`NR1`), exibindo as colunas essenciais de identificação (produto e família), comprador responsável, forma de abastecimento e status.

---

## 2. SQL Principal
```sql
SELECT * FROM (
    WITH PRODUTOS_FORNECEDOR AS (
        SELECT /*+ MATERIALIZE */
            P.SEQPRODUTO,
            P.DESCCOMPLETA,
            P.SEQFAMILIA
        FROM MAP_PRODUTO P
        INNER JOIN MAP_FAMFORNEC FF 
            ON FF.SEQFAMILIA = P.SEQFAMILIA
        WHERE (NVL(:NR1, 0) = 0 OR FF.SEQFORNECEDOR = :NR1)
    ),
    STATUS_EMPRESA_15 AS (
        SELECT /*+ MATERIALIZE */
            PE.SEQPRODUTO,
            PE.STATUSCOMPRA,
            PE.FORMAABASTECIMENTO
        FROM MRL_PRODUTOEMPRESA PE
        INNER JOIN PRODUTOS_FORNECEDOR PF 
            ON PF.SEQPRODUTO = PE.SEQPRODUTO
        WHERE PE.NROEMPRESA = 15
          AND PE.STATUSCOMPRA = 'A'
    )
    SELECT DISTINCT
        PF.SEQPRODUTO,
        PF.DESCCOMPLETA,
        PF.SEQFAMILIA,
        NVL(COMP.APELIDO, COMP.COMPRADOR) AS APELIDO_COMPRADOR,
        NVL(SE.FORMAABASTECIMENTO, FD.FORMAABASTECIMENTO) AS FORMA_ABASTECIMENTO,
        SE.STATUSCOMPRA AS STATUS_EMPRESA_15
    FROM PRODUTOS_FORNECEDOR PF
    INNER JOIN STATUS_EMPRESA_15 SE 
        ON SE.SEQPRODUTO = PF.SEQPRODUTO
    LEFT JOIN MAP_FAMDIVISAO FD 
        ON FD.SEQFAMILIA = PF.SEQFAMILIA 
       AND FD.NRODIVISAO = 1
    LEFT JOIN MAX_COMPRADOR COMP 
        ON COMP.SEQCOMPRADOR = FD.SEQCOMPRADOR
    ORDER BY
        PF.DESCCOMPLETA ASC
)
```

---

## 3. Variáveis para Cadastrar em `Var - F7`

| Variável | Tipo | Descrição | Valor Padrão | Instrução |
| :--- | :--- | :--- | :--- | :--- |
| **`NR1`** | Numérico | Código do Fornecedor (0 = Todos) | `0` | Digite o código do fornecedor ou `0` para trazer todos os produtos ativos |

---

## 4. Passo a Passo de Configuração no Totvs Consinco

1. Acesse o ERP Totvs Consinco no módulo **SGI > Consulta Criação**.
2. Cole o código do **SQL Principal** no editor de consultas.
3. Pressione o botão **`Var - F7`** no menu superior da tela.
4. Cadastre a variável:
   - **Nome**: `NR1`
   - **Tipo**: `Numérico`
   - **Descrição**: `Código do Fornecedor (0 = Todos)`
   - **Valor Padrão**: `0`
5. Clique em **OK** para salvar a configuração de variáveis.
6. Pressione **Executar (`F8`)**, informe o código do fornecedor no filtro e visualize o resultado.
