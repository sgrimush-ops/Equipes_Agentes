# Aprendizado: Pendências de Transferência (Ped Receber) e Notas Fiscais Fantasmas

Este documento consolida as melhores práticas para calcular o saldo de transferências pendentes ("Ped Receber") no ERP Totvs Consinco, especificamente ao cruzar as remessas do Centro de Distribuição (CD) com os recebimentos das Lojas, sem perder desempenho e garantindo a exatidão dos dados operacionais reais.

## 1. O Problema das "Notas Fantasmas" (Pedidos Pendentes Antigos)

No Consinco, a visão `MAXV_MSUPEDIDOSUPRIMEXP` (expedições) e a view `MFLV_BASEDFITEM` (itens faturados em trânsito) contêm o histórico de transferências entre filiais.

Muitas vezes, inserimos filtros de data (ex: `DTAEMISSAO >= TRUNC(SYSDATE) - 180`) nessas views visando melhorar a performance da consulta. No entanto, **nunca aplique filtros de data retroativos artificiais** ao calcular a métrica de "Ped Receber" do sistema.

**Por quê?**
Sistemas de varejo frequentemente acumulam pedidos ou Notas Fiscais de transferência "fantasmas" que nunca foram recebidos eletronicamente pela filial destino. Se essas operações tiverem mais de 180 dias, o filtro de data as ocultará da query, fazendo com que ela exiba `0` pendências, enquanto a tela oficial do sistema (que calcula sem filtro de data) exibe os saldos fantasmas antigos. A query customizada **deve refletir a tela do ERP fielmente**.

## 2. Solução de Performance: Tabela Base vs View

Remover o filtro de `DTAEMISSAO` faz a query escanear anos de faturamento e resulta em lentidão extrema, especialmente quando se utiliza a view complexa de retaguarda `MLFV_BASENFE` dentro de um `NOT EXISTS` que avalia se a loja destino já deu entrada na Nota Fiscal.

**A Solução de Performance:**
* **Substituir a view `MLFV_BASENFE` pela tabela física `MLF_NOTAFISCAL`.**
* A tabela `MLF_NOTAFISCAL` permite acessos indexados rápidos através das suas chaves primárias.
* Quando usada no bloco `NOT EXISTS`, o otimizador Oracle realiza buscas diretas muito rápidas, tornando o filtro de `DTAEMISSAO` totalmente desnecessário e recuperando a exatidão histórica sem penalizar o banco de dados.

## 3. Atenção aos Nomes de Coluna nos Joins (`SEQNF` vs `SEQNOTAFISCAL`)

Ao juntar itens faturados (`MFLV_BASEDFITEM`) com a capa da nota (`MLF_NOTAFISCAL`), ocorre um erro comum de mapeamento:

* **O Erro:** `I.SEQNF = N.SEQNOTAFISCAL`
Embora a tabela `MLF_NOTAFISCAL` possua a coluna `SEQNOTAFISCAL` (que é única globalmente), a coluna `SEQNF` da view `MFLV_BASEDFITEM` na verdade se relaciona de forma direta e segmentada com a coluna **`SEQNF`** da tabela `MLF_NOTAFISCAL`. Fazer o join cruzado silenciosamente invalida as amarrações e zera os resultados em trânsito das notas recentes (pois os IDs divergem, mesmo sem gerar o erro lógico ORA-00904).

* **A Ligação Correta:**
```sql
FROM MFLV_BASEDFITEM I
INNER JOIN MLF_NOTAFISCAL N 
   ON I.NROEMPRESA = N.NROEMPRESA 
  AND I.SEQNF = N.SEQNF 
  AND I.TIPNOTAFISCAL = N.TIPNOTAFISCAL 
  AND I.SERIEDF = N.SERIENF 
  AND I.NUMERODF = N.NUMERONF 
  AND I.SEQPESSOA = N.SEQPESSOA
```

## 4. Estrutura do NOT EXISTS (Validando o Recebimento)

Para atestar que uma nota emitida pelo CD (`TIPNOTAFISCAL = 'S'`) ainda não foi recebida pela Loja de destino, usamos a própria tabela `MLF_NOTAFISCAL` referenciando as chaves de rastreabilidade do Consinco:

```sql
AND NOT EXISTS (
    SELECT 1
    FROM MLF_NOTAFISCAL R
    WHERE R.SEQAUXNOTAFISCALORIGEM = N.SEQAUXNOTAFISCAL
      AND R.TIPNOTAFISCAL = 'E'
      AND R.STATUSNF != 'C'
)
```
**Nota:** A coluna `SEQAUXNOTAFISCAL` da tabela de saída (`N`) é o elo rastreável usado pela tabela de entrada (`R`) no campo `SEQAUXNOTAFISCALORIGEM`. Sem essa correlação exata, todas as notas históricas continuarão marcadas como "em trânsito", gerando pendências irreais (falsos positivos de pendência).
