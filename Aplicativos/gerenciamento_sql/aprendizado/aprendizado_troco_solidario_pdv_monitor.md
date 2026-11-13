# Aprendizado: Auditoria e Ranking de Troco Solidário no PDV (`CONSINCOMONITOR.TB_DOCTOTROCOSOLIDARIO`)

## 1. Contexto e Descoberta Arquitetural
No ERP Totvs Consinco integrado ao **AcruxMonitor / Consinco PDV**, a operação de **Troco Solidário** (doação realizada pelo cliente no frente de caixa para uma instituição de caridade) é registrada simultaneamente em duas camadas do banco de dados Oracle, mas **apenas uma delas deve ser utilizada** como fonte primária para evitar duplicidade:

1. **Fonte Primária Oficial e em Tempo Real (`CONSINCOMONITOR.TB_DOCTOTROCOSOLIDARIO`):**
   - Toda doação de Troco Solidário nasce no schema **`CONSINCOMONITOR`**, unida pela chave primária composta `(NROEMPRESA, NROCHECKOUT, SEQDOCTO)`:
     - **`CONSINCOMONITOR.TB_DOCTOTROCOSOLIDARIO TS`**:
       - `TS.NROEMPRESA`, `TS.NROCHECKOUT`, `TS.SEQDOCTO`
       - `TS.SEQPESSOA`: Código da **Instituição de Caridade** beneficiada (cruza diretamente com `CONSINCO.GE_PESSOA.SEQPESSOA` -> `NOMERAZAO`).
       - `TS.SEQDOCTOORIGEM`: Aponta para o `SEQDOCTO` do cupom de venda original onde surgiu o troco.
     - **`CONSINCOMONITOR.TB_DOCTO D`**:
       - `D.DTAMOVIMENTO`: Data do movimento do caixa.
       - `D.DTAHOREMISSAO`: Data e hora exatas da doação.
       - `D.COO`: Número do comprovante emitido no PDV.
       - `D.SEQUSUARIO`: ID exato da **Operadora de Caixa** que recebeu a doação (cruza diretamente com `CONSINCO.GE_USUARIO.SEQUSUARIO` -> `CODUSUARIO` e `NOME`).
       - **Atenção (`ORA-00904`):** Na tabela real `CONSINCOMONITOR.TB_DOCTO`, a coluna de empresa chama-se apenas **`NROEMPRESA`**. A coluna `NROEMPRESAERP` existe apenas na tabela temporária `MONX_DOCTO` do schema `CONSINCO` e nunca deve ser referenciada em `TB_DOCTO`.
     - **`CONSINCOMONITOR.TB_DOCTOPAGTO P`**:
       - `SUM(NVL(P.VLRTOTAL, NVL(P.VALOR, 0)))`: Valor financeiro (R$) efetivamente doado no Troco Solidário.
       - Deve-se exigir `NVL(P.STATUS, 'A') != 'C'`.
     - **`CONSINCOMONITOR.TB_DOCTOESTORNO EST`**:
       - Para expurgar doações estornadas/canceladas no PDV sem usar loops `NOT EXISTS`, faça `LEFT JOIN CONSINCOMONITOR.TB_DOCTOESTORNO EST` pela PK `(NROEMPRESA, NROCHECKOUT, SEQDOCTO)` exigindo `EST.SEQDOCTO IS NULL`.

2. **Por que NÃO unir com `CONSINCO.FI_TSMOVENTRADAOUTROSOPER` ou `MFL_FINANCEIRO` (Prevenção de Duplicidade):**
   - Após o fechamento do movimento de caixa, o ERP replica os lançamentos da `TB_DOCTOTROCOSOLIDARIO` para a tabela de Outras Entradas da Tesouraria (`CONSINCO.FI_TSMOVENTRADAOUTROSOPER` vinculada a `FI_TSCODMOVTOENTRADA`), porém gravando `NROCUPOM` nulo ou agrupado e sem os movimentos dos caixas ainda abertos no dia.
   - Se uma consulta fizer `UNION ALL` entre `TB_DOCTOTROCOSOLIDARIO` e `FI_TSMOVENTRADAOUTROSOPER`, todas as operadoras terão seus valores e quantidades de doações **duplicados**.
   - Portanto, toda consulta de Troco Solidário e Ranking de Operadoras deve ler **exclusivamente** da **`CONSINCOMONITOR.TB_DOCTOTROCOSOLIDARIO`** (+ `TB_DOCTO` + `TB_DOCTOPAGTO` - `TB_DOCTOESTORNO`).

---

## 2. Padrão da Query Oficial (`levantamento_troco_solidario.sql`)
- **Arquivo SQL:** `Aplicativos/gerenciamento_sql/querys/levantamento_troco_solidario.sql`
- **Configuração `Var - F7`:** `Aplicativos/gerenciamento_sql/Var-F7/levantamento_troco_solidario.md`
  - `:DT1` (Data Inicial)
  - `:DT2` (Data Final)
  - `:LT1` (Lojas separadas por vírgula ou `0` para todas as lojas da lista branca `1..8, 11..15, 17, 18`)
- **Colunas Entregues:** `RANKING`, `LOJA`, `ID_OPERADOR`, `LOGIN_OPERADORA`, `NOME_OPERADORA`, `COD_INSTITUICAO`, `INSTITUICAO_BENEFICIADA`, `QTD_DOACOES`, `VLR_TOTAL_ARRECADADO`, `DOACAO_MEDIA`, `MAIOR_DOACAO`, `PERIODO_CAPTURADO` (sem coluna de percentual de participação), com fechamento na última linha `TOTAL GERAL ->`.

