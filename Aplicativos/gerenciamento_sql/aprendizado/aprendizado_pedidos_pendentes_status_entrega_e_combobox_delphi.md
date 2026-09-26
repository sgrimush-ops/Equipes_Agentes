# Aprendizado: Status de Entrega, Soberania do Item e ComboBox sem Truncamento no Delphi (Consinco)

## Contexto
Na criação e manutenção de consultas de pedidos de compras e suprimentos (`MSU_PEDIDOSUPRIM`, `MSU_PSITEMRECEBER`, `MSU_PSITEMRECEBIDO`), surgem desafios críticos de regras de negócio de entrega, identificação de cancelamentos individuais e limitações do driver Delphi do ERP Totvs Consinco.

---

## 1. Falha de Truncamento em Listas (`LSx`) no Delphi e a Solução `DECODE` + `CONNECT BY`

### O Problema:
Ao tentar gerar listas estáticas compactas usando coleções Oracle:
```sql
-- NÃO USAR: Trunca para 3 letras no Delphi!
SELECT COLUMN_VALUE FROM TABLE(SYS.ODCIVARCHAR2LIST('TODOS','TOT_ATEND','ATEND_PARC','NÃO_ATENDIDO','ATRASO','AGUARDANDO'))
```
O driver Delphi/BDE do Consinco não interpreta o tipo de coleção dinâmico `TABLE OF VARCHAR2(4000)` e aloca um buffer incorreto, cortando todos os textos do ComboBox para exatamente 3 caracteres (`AGU`, `ATE`, `ATR`, `NÃO`, `TOD`, `TOT`).

### A Solução Padrão Ouro (127 caracteres):
Usar geração tabular com `DECODE` e `CONNECT BY LEVEL`:
```sql
SELECT DECODE(LEVEL,1,'TODOS',2,'TOT_ATEND',3,'ATEND_PARC',4,'NÃO_ATENDIDO',5,'ATRASO',6,'AGUARDANDO') FROM DUAL CONNECT BY LEVEL<=6
```
- **Vantagem 1:** O Delphi dimensiona o `TStringField` com base no maior argumento do `DECODE` (`NÃO_ATENDIDO` = 12 chars), exibindo todas as opções inteiras.
- **Vantagem 2:** Respeita com folga o limite físico rígido de 145 caracteres do campo SQL no `Var - F7` do Consinco.
- **Vantagem 3:** Mantém `'TODOS'` como o primeiro item da lista.

---

## 2. Soberania do Status do Item (`STATUSITEM`) sobre a Capa (`SITUACAOPED`)

### Realidade Operacional de Varejo / CD:
No fluxo de suprimentos do Totvs Consinco:
- A capa do pedido (`MSU_PEDIDOSUPRIM.SITUACAOPED`) só muda para `'C'` (Cancelado) se **todo** o pedido for cancelado. Se 10 itens forem cancelados e 1 permanecer ativo ou atendido, a capa continua `'A'` (Aberto).
- Portanto, exibir `STATUS_PEDIDO` na visão de itens gera falsos positivos e confusão para os compradores.
- **Padrão Obrigatório:** Utilizar e expor o **`STATUS_ITEM`** vindo de `MSU_PSITEMRECEBER.STATUSITEM`:
  - `'A' -> 'A - ATIVO'`
  - `'C' -> 'C - CANCELADO'`
  - `'L' -> 'L - LIQUIDADO'`
  - `'P' -> 'P - PARCIAL'`

---

## 3. Matriz de Classificação do `STATUS_ENTREGA`

Para classificar com exatidão a situação operacional de atendimento das linhas de pedido:

```sql
CASE
    WHEN NVL(I.QUANTIDADE_PEDIDA, 0) > 0 AND NVL(REC.QUANTIDADE_ATENDIDA, 0) >= I.QUANTIDADE_PEDIDA THEN 'TOT_ATEND'
    WHEN NVL(REC.QUANTIDADE_ATENDIDA, 0) > 0 AND NVL(REC.QUANTIDADE_ATENDIDA, 0) < NVL(I.QUANTIDADE_PEDIDA, 0) THEN 'ATEND_PARC'
    WHEN C.DTALIMITERECEBTO IS NOT NULL AND TRUNC(C.DTALIMITERECEBTO) < TRUNC(SYSDATE) THEN 'NÃO_ATENDIDO'
    WHEN C.DTARECEBTO IS NOT NULL AND TRUNC(C.DTARECEBTO) < TRUNC(SYSDATE) THEN 'ATRASO'
    ELSE 'AGUARDANDO'
END AS STATUS_ENTREGA
```

### Regras:
1. **`TOT_ATEND`**: Atendimento integral (>= 100%).
2. **`ATEND_PARC`**: Atendimento parcial (> 0 e < 100%), independente do vencimento de datas.
3. **`NÃO_ATENDIDO`**: Atendimento zero com data limite (`DTALIMITERECEBTO`) vencida em relação ao `SYSDATE`.
4. **`ATRASO`**: Atendimento zero com data de previsão (`DTARECEBTO`) vencida, porém ainda dentro do prazo limite.
5. **`AGUARDANDO`**: Atendimento zero dentro do prazo de entrega.

---

## 4. Filtro Opcional de Data Limite no Topo da Pirâmide (`:DT3`)

Para permitir que o usuário filtre pedidos cuja data limite de recebimento seja "até" uma data específica (ou traga todos quando o campo for deixado em branco):

```sql
AND (:DT3 IS NULL OR TRUNC(P.DTALIMITERECEBTO) <= TRUNC(:DT3))
```
Aplicado diretamente na primeira CTE materializada (`CAPA_PEDIDOS`), garantindo máxima performance de corte inicial.
