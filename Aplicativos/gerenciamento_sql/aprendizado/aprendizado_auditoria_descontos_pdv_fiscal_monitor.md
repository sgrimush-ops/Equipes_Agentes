# Aprendizado: Auditoria de Descontos de PDV (Fiscal de Caixa vs. Automático / Sistema e Schema CONSINCOMONITOR)

## 1. Contexto e Descoberta Arquitetural
No ERP Totvs Consinco integrado com o **AcruxMonitor / Consinco PDV (`PDVORIGEM = 1`)**, a identificação de descontos concedidos no frente de caixa divide-se entre duas camadas distintas do banco de dados Oracle:

### A. Por que `CONSINCO.MFL_CUPOMFISCAL.SEQSUPERVISOR` não mostra o Fiscal de Caixa?
1. Na integração padrão do PDV para `CONSINCO.MFL_CUPOMFISCAL`, o sistema replica o código do Operador de Caixa (`CF.SEQOPERADOR`) dentro da coluna `CF.SEQSUPERVISOR` em 100% dos cupons (`CF.SEQSUPERVISOR = CF.SEQOPERADOR`).
2. Na tabela `CONSINCO.MFL_OPERADOR`, a coluna `CODOPERADOR` permanece nula e a chave `SEQOPERADOR` aponta diretamente para **`CONSINCO.GE_USUARIO.SEQUSUARIO`** (`CODUSUARIO` = Login e `NOME` = Nome Completo do colaborador).
3. Na tabela de decomposição fiscal de descontos do item (`CONSINCO.MFL_DFITEMACRESCDESCTO`), os descontos manuais de diferença de preço no item (`mtDescontoItemDiferencaPreco`) **são absorvidos dentro do código `SEQTIPOACRESCDESCTO = 21` (*Desconto por incentivo no item*)**, deixando o código `SEQTIPOACRESCDESCTO = 2` (*Desconto no item*) zerado na `MFL_DFITEMACRESCDESCTO`.

### B. Onde fica salvo quem foi o Fiscal de Caixa que autorizou o desconto com senha?
A auditoria real de senhas de Fiscais de Caixa / Supervisores fica armazenada no schema **`CONSINCOMONITOR`**, nas tabelas de **Log de Segurança do PDV**, unidas pela chave primária composta `(NROEMPRESA, NROCHECKOUT, SEQLOGSEGPDV)`:
1. **`CONSINCOMONITOR.TB_LOGSEGURANCAPDV`**:
   - `SEQUSUARIO`: ID exato do Fiscal de Caixa que digitou a senha/crachá (cruza diretamente com `CONSINCO.GE_USUARIO.SEQUSUARIO`).
   - `DTAHOREMISSAO`: Data e hora exatas da liberação da senha no PDV.
   - `METODO`: Identifica a operação liberada pelo Fiscal:
     - `'mtDescontoItemDiferencaPreco'`: Desconto manual / diferença de preço concedida no item (Código `02`).
     - `'mtDescontoCupom'`: Desconto manual concedido no subtotal do cupom (Código `01`).
2. **`CONSINCOMONITOR.TB_LOGSEGDOCTOPDV`**:
   - Relaciona o log ao documento fiscal do PDV via `DTAMOVIMENTO`, `SERIE`, `CRO` e `COO` (onde `COO = MFL_CUPOMFISCAL.NUMERODF`).
3. **`CONSINCOMONITOR.TB_LOGSEGITEMPDV`**:
   - Relaciona o log ao item específico do cupom via `SEQITEM` (onde `SEQITEM = MFL_CUPOMFISCAL.SEQITEMDF`).
4. **`CONSINCOMONITOR.TB_LOGSEGVALORPDV`**:
   - Armazena em `VALOR` o valor financeiro (R$) do desconto autorizado pelo Fiscal.

---

## 2. Regras de Ouro de Negócio e Performance

1. **Filtro Estrito de Vendas Válidas Consumadas no PDV (`INNER JOIN MFL_CUPOMFISCAL`):**
   - O log de segurança (`TB_LOGSEGURANCAPDV`) registra o momento em que o Fiscal digita a senha, mesmo que segundos depois o item ou o cupom seja cancelado/abortado no caixa (ex: quando o Fiscal digita o valor errado, cancela o item e lança novamente o valor correto).
   - Para auditar descontos efetivos (fatos consumados), faça sempre `INNER JOIN CONSINCO.MFL_CUPOMFISCAL CF` exigindo `CF.STATUSCF != 'C'` e `CF.STATUSITEM != 'C'`.

2. **Detecção de Auto-Liberação (`Operador de Caixa = Fiscal Autorizador`):**
   - Sempre compare `CF.SEQOPERADOR` (Operador logado no PDV) com `S.SEQUSUARIO` (Fiscal que digitou a senha de liberação). Quando `CF.SEQOPERADOR = S.SEQUSUARIO`, sinalize `'SIM (OPERADOR = FISCAL)'`, permitindo auditar auto-liberações em vendas de atacado/grande volume.

3. **Separação Arquitetural entre Consulta Detalhada e Consulta Consolidada (Sem `LS1`):**
   - **Relatório Detalhado (`auditoria_descontos_fiscal_detalhada.sql`):** Deve ser exclusivo para **Descontos Manuais de Fiscal de Caixa** (`TB_LOGSEGURANCAPDV`), usando apenas `:DT1`, `:DT2` e `:LT1` (sem `LS1`). Nunca tente listar item a item os descontos automáticos (`21 - Incentivo no item`) no relatório detalhado, pois há mais de 750.000 itens promocionais em 30 dias.
   - **Relatório Consolidado por Tipo de Operação (`auditoria_descontos_fiscal_ranking.sql`):** Parte da tabela mestre `CONSINCO.MFL_TIPOACRESCDESCTO T` (`WHERE NVL(T.INDTIPOACRESCDESCTO, 'D') = 'D'`) com `LEFT JOIN` para o resumo de `MFL_DOCTOFISCAL D` + `MFL_DFITEMACRESCDESCTO A` (unidos obrigatoriamente por **`A.SEQNF = D.SEQNF AND A.NROEMPRESA = D.NROEMPRESA`**).
   - **Reclassificação Contábil entre Código `2` e Código `21` no Consolidado:** Como o PDV joga os descontos manuais de item dentro do código `21` na `MFL_DFITEMACRESCDESCTO`, o relatório consolidado injeta o valor apurado no `TB_LOGSEGURANCAPDV` (`mtDescontoItemDiferencaPreco` em cupons válidos) na linha **`2 - DESCONTO NO ITEM`** e subtrai esse mesmo montante da linha **`21 - DESCONTO POR INCENTIVO NO ITEM`**, garantindo que todos os tipos apareçam com seus valores reais e que o `TOTAL GERAL ->` feche com exatidão.
   - **Coluna `Q_LOJAS` via `LISTAGG` Pré-Agrupado:** Para listar quais lojas deram cada tipo de desconto (`Q_LOJAS` ao lado de `QTD_LOJAS`), agrupe primeiro por `(SEQTIPOACRESCDESCTO, NROEMPRESA)` em uma CTE materializada e só depois aplique `LISTAGG(TO_CHAR(NROEMPRESA), ', ') WITHIN GROUP (ORDER BY NROEMPRESA)`.

4. **Atenção aos Nomes Oficiais de Colunas no Dicionário Consinco:**
   - Em `MFL_CUPOMFISCAL`: o código do produto é **`CF.CODPRODUTO`** (e não `SEQPRODUTO`).
   - Em `MFL_TIPOACRESCDESCTO`: a descrição é **`T.TIPOACRESCDESCTO`** (e não `DESCRICAO`).
   - Em `MFL_DFITEMACRESCDESCTO`: o valor do desconto é **`A.VALOR`** (e não `VLRACRESCDESCTO`), e o join com `MFL_DOCTOFISCAL` é por **`A.SEQNF = D.SEQNF AND A.NROEMPRESA = D.NROEMPRESA`**.
