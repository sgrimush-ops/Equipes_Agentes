# Aprendizado: Comparativo de Estoque WMS vs ERP Comercial & Expurgo Dinâmico de Departamentos

## 1. Contexto e Objetivo de Negócio
No ERP Totvs Consinco (módulo Logística WMS), a tela padrão de auditoria e conferência de inventário **`LOG0085`** (`frmComparEstoque`) impõe um bloqueio operacional durante o horário de expediente/movimentação, impedindo que a equipe de auditoria e logística audite o estoque em tempo real.

Para contornar este bloqueio sem gerar impacto de lock no banco de dados Oracle, foi desenvolvida a consulta customizada em **Consulta Criação** (`comparativo_estoque_wms_vs_erp.sql`), cruzando a posição dos endereços físicos do WMS com a posição de estoque comercial do ERP e adicionando a apuração de cargas em trânsito/processamento (Recebimento e Separação).

---

## 2. Arquitetura Canônica de Tabelas (WMS x ERP)

| Visão | Tabelas Utilizadas | Granularidade / Campos Críticos | Regra de Negócio |
|---|---|---|---|
| **Estoque ERP Comercial** | `MRL_PRODUTOEMPRESA PE` | `NROEMPRESA`, `SEQPRODUTO`<br>`ESTQDEPOSITO`, `ESTQTROCA`, `ESTQOUTRO` | Saldo oficial registrado no módulo comercial. O estoque que o WMS deve espelhar é estritamente o **`ESTQDEPOSITO`** do CD. |
| **Reservas Comerciais ERP** | `MRL_PRODUTOEMPRESA PE` | `QTDRESERVADAVDA + QTDRESERVADARECEB + QTDRESERVADAFIXA + QTDRESERVADAFISC` | `ESTQGERENCIAL` **não existe** em `MRL_PRODUTOEMPRESA`. A soma dos campos de reserva fornece o total bloqueado comercialmente. |
| **Estoque Físico WMS** | `MLO_ENDERECO X` | `NROEMPRESA`, `SEQPRODUTO`, `ESPECIEENDERECO`, `QTDATUAL` | Saldos alocados nas posições de picking/apanha (`ESPECIEENDERECO = 'A'`), aéreo/pulmão (`'P'`) e especiais (`OUTROS`). |
| **Cargas em Recebimento** | `MLO_CARGARECEB C`<br>`MLO_CARGARECPROD RP` | `C.STATUSCARGA`, `C.STATUSARMAZENAGEM`<br>`RP.QTDTOTALDOCUMENTO` | Produtos conferidos fisicamente cuja NF já entrou no ERP, mas a carga ainda está pendente de armazenagem física no WMS (`STATUSCARGA = 'L'` e `STATUSARMAZENAGEM != 'A'` ou em conferência `'R'`). |
| **Cargas em Separação** | `MLO_CARGAEXPED E`<br>`MLO_CARGAEXPPROD EP` | `E.STATUSCARGA = 'L'`<br>`EP.QTDEMBSOLICITADA * EP.QTDEMBALAGEM` | Itens já reservados para expedição/saída com carga liberada. |
| **Departamento Ativo (Nível 1)** | `MAP_FAMDIVCATEG X`<br>`MAP_CATEGORIA Y` | `Y.NIVELHIERARQUIA = 1`, `Y.TIPCATEGORIA = 'M'`, `X.STATUS = 'A'` | Retorna o departamento mercadológico ativo no nível 1 da família (`X.NRODIVISAO = 1`). |

---

## 3. Padrão de Granularidade Unificada (`FULL OUTER JOIN`)

Como um produto pode existir com saldo apenas no ERP (e zero no WMS), ou apenas no WMS (e zero no ERP), ou ter cargas em trânsito sem saldo em estoque, a base de produtos deve ser gerada por um **`FULL OUTER JOIN`** em CTE materializada:

```sql
CTE_BASE_PRODUTOS AS (
    SELECT /*+ MATERIALIZE */
        DISTINCT
        COALESCE(E.NROEMPRESA, W.NROEMPRESA, R.NROEMPRESA, S.NROEMPRESA) AS NROEMPRESA,
        COALESCE(E.SEQPRODUTO, W.SEQPRODUTO, R.SEQPRODUTO, S.SEQPRODUTO) AS SEQPRODUTO
    FROM CTE_ESTOQUE_ERP E
    FULL OUTER JOIN CTE_WMS_ENDERECO W 
        ON W.NROEMPRESA = E.NROEMPRESA 
       AND W.SEQPRODUTO = E.SEQPRODUTO
    FULL OUTER JOIN CTE_RECEBIMENTO_PENDENTE R 
        ON R.NROEMPRESA = COALESCE(E.NROEMPRESA, W.NROEMPRESA) 
       AND R.SEQPRODUTO = COALESCE(E.SEQPRODUTO, W.SEQPRODUTO)
    FULL OUTER JOIN CTE_SEPARACAO_PENDENTE S 
        ON S.NROEMPRESA = COALESCE(E.NROEMPRESA, W.NROEMPRESA, R.NROEMPRESA) 
       AND S.SEQPRODUTO = COALESCE(E.SEQPRODUTO, W.SEQPRODUTO, R.SEQPRODUTO)
)
```

---

## 4. Prevenção de Truncamento Delphi em Listas `LSx` (`Var - F7`)

### O Problema:
Ao utilizar coleções Oracle do tipo `SYS.ODCIVARCHAR2LIST('TODOS', 'ALINHADO', 'DIVERGENCIA')` em uma instrução SQL da lista `LS1`, o driver de banco Delphi/BDE infere o tamanho da coluna pelo primeiro item (`TODOS` = 5 caracteres, ou 3 caracteres se for `TOD`), truncando os textos restantes para `DIV`, `SOB`, `REC` na tela de seleção.

### Soluções Homologadas:
1. **Opção A — Constantes Literais (Recomendada):**
   Cadastrar as opções diretamente no campo da instrução sem `SELECT`, separadas por ponto-e-vírgula:
   ```text
   TODOS;ALINHADO;DIVERGENCIA;SOBRA ERP;SOBRA WMS;RECEBIMENTO
   ```
2. **Opção B — SQL com `CAST` Explícito:**
   Se precisar de query SQL, forçar o tipo `VARCHAR2(50)`:
   ```sql
   SELECT CAST(COLUMN_VALUE AS VARCHAR2(50)) FROM TABLE(SYS.ODCIVARCHAR2LIST('TODOS','ALINHADO','DIVERGENCIA','SOBRA ERP','SOBRA WMS','RECEBIMENTO'))
   ```

---

## 5. Expurgo Dinâmico de Departamentos Multi-Termos (`LT2`)

### O Desafio:
O usuário informa termos como `almoxarifado, nao alimento, servico` em uma variável de texto `LT2`. Os nomes no banco de dados podem estar com acentos (`NÃO ALIMENTOS`, `SERVIÇOS`), maiúsculas/minúsculas e espaçamentos variados. Além disso, se o usuário informar `0` ou `NENHUM`, nenhum departamento deve ser expurgado.

### Solução com Transliteração e Regex:
```sql
AND (
    NVL(TRIM(:LT2), '0') IN ('0', 'NENHUM', '')
    OR NOT REGEXP_LIKE(
        REPLACE(TRANSLATE(UPPER(NVL(DEP.DEPARTAMENTO, 'X')), 'ÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ', 'AEIOUAEIOUAOAEIOUC'), ' ', ''),
        REPLACE(REPLACE(TRANSLATE(UPPER(TRIM(:LT2)), 'ÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ', 'AEIOUAEIOUAOAEIOUC'), ' ', ''), ',', '|'),
        'i'
    )
)
```

---

## 6. Prevenção de Erros ORA Críticos em CTEs

1. **`ORA-00904: "PE"."ESTQGERENCIAL": invalid identifier`:**
   - **Causa:** Tentar consultar `ESTQGERENCIAL` em `MRL_PRODUTOEMPRESA`.
   - **Solução:** Utilizar a soma dos campos canônicos de reserva: `QTDRESERVADAVDA + QTDRESERVADARECEB + QTDRESERVADAFIXA + QTDRESERVADAFISC`.
2. **`ORA-00904: "E"."ESTQTROCA": invalid identifier`:**
   - **Causa:** A CTE `CTE_ESTOQUE_ERP` apelidou a coluna de `ESTQ_TROCA_ERP`, mas no bloco externo foi chamado `E.ESTQTROCA`.
   - **Solução:** Garantir alinhamento estrito 1-para-1 entre os aliases definidos no `SELECT` das CTEs e os nomes acessados nas CTEs consumidoras.
