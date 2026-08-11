# Aprendizado: Auditoria de Preços, Promoções e a Tabela MAD_PRODLOGPRECO

Este documento registra o conhecimento adquirido ao construir e investigar a query de histórico de alterações de preços no ecossistema Totvs Consinco SGI, revelando o comportamento interno do motor de promoções e o "Efeito Cascata" na frente de caixa.

## Tabela Oficial de Histórico (Auditoria Fina de Preços)
Apesar do sistema contar com logs gerais (`MAP_AUDITORIA`), a tela nativa "Preços por Segmento" utiliza a tabela altamente especializada **`MAD_PRODLOGPRECO`** para formar o grid "Histórico das Alterações de Preço".
- Ela armazena informações cruciais como: `USUALTERACAO`, `PRECO`, `TIPOALTPRECO` ('N' Normal, 'P' Promocional), `PROCESSOALTERACAO` e `MOTIVOALTMANUAL`.
- Para puxar as informações corretas e espelhar a tela nativa, deve-se filtrar `INDGERAPRECO != 'I'` e garantir que a alteração não foi reprovada (`APROVADOREPROVADO = 'A' OR APROVADOREPROVADO IS NULL`).

## O "Efeito Cascata" do Fim de Promoção
As investigações sobre itens que repentinamente passam por valores muito baixos na frente de caixa (geralmente preços antigos de importação de carga) revelaram o seguinte mecanismo sistêmico:

1. **O Registro Automático de Valor Zero:**
   Quando uma promoção chega à sua data de vencimento, o preço promocional não é deletado. Em vez disso, durante a madrugada, o robô do sistema (usuário `AUTOMATICO`) insere um novo registro em `MAD_PRODLOGPRECO` com **`PRECO = 0`** e `TIPOALTPRECO = 'P'`.
   - Regra de Negócio: No Consinco, **Preço Promocional = 0 significa "Promoção Inativa"**. É esse registro que "derruba" a vigência do desconto no PDV.

2. **Queda para o Preço Normal (Fallback):**
   A fórmula oficial de preço praticado no Consinco é tentar sempre o Preço Promocional primeiro (`NVL(NULLIF(PRECOVALIDPROMOC, 0), PRECOVALIDNORMAL)`). 
   - Se o item estava sendo vendido apenas com promoções consecutivas emendadas, a equipe tende a "esquecer" de atualizar o preço Normal.
   - Quando a última promoção vence e o sistema lança o `0`, o PDV faz o fallback automático e encontra o último preço Normal cadastrado (que pode ser um valor defasado de anos atrás, como o da implantação inicial).
   - **Solução de Negócio**: O Preço Normal deve sempre estar atualizado para evitar esse mergulho no PDV em produtos que "vivem de promoção".

## Query Canônica de Auditoria Livre (Consulta Criação / Var - F7)
Esta query é a recriação fiel do mecanismo da tela nativa, ideal para uso na Consulta Criação pois já inclui a variável de produto (`NR1`) e o filtro opcional de loja (`NR2` sentinela 0), além de contornar o bloqueador (SELECT fantasma externo).

```sql
SELECT * FROM (
    SELECT 
        A.NROEMPRESA AS LOJA,
        A.NROSEGMENTO AS SEGMENTO,
        A.QTDEMBALAGEM AS EMBALAGEM,
        CASE A.TIPOALTPRECO 
            WHEN 'N' THEN 'Normal' 
            WHEN 'P' THEN 'Promocional' 
            ELSE A.TIPOALTPRECO 
        END AS TIPO_PRECO,
        TO_CHAR(A.DTAHORALTERACAO, 'DD/MM/YYYY HH24:MI:SS') AS DATA_HORA,
        A.USUALTERACAO AS USUARIO_ALT,
        A.PRECO,
        CASE 
            WHEN A.MOTIVOALTMANUAL IS NOT NULL THEN A.PROCESSOALTERACAO || ' - ' || A.MOTIVOALTMANUAL 
            ELSE A.PROCESSOALTERACAO 
        END AS MOTIVO,
        TO_CHAR(A.DTAHORAPROVREPROV, 'DD/MM/YYYY HH24:MI:SS') AS APROVACAO,
        A.USUAPROVREPROV AS USUARIO_APROV,
        TO_CHAR(A.DTAPROGALTERACAO, 'DD/MM/YYYY') AS DTA_PROGRAM
    FROM MAD_PRODLOGPRECO A
    WHERE A.SEQPRODUTO = :NR1 
      AND (NVL(:NR2, 0) = 0 OR A.NROEMPRESA = :NR2)
      AND A.INDGERAPRECO != 'I'
      AND (A.APROVADOREPROVADO = 'A' OR A.APROVADOREPROVADO IS NULL)
    ORDER BY A.DTAHORALTERACAO DESC, A.DTAHORAPROVREPROV DESC
)
```
