# Procedimento Var - F7: Pedidos Pendentes Fornecedor CD (v2)

## Objetivo
Consulta de pedidos de compras/suprimentos (`MSU_PEDIDOSUPRIM` e `MSU_PSITEMRECEBER`) detalhando quantidades pedidas, atendidas, percentual de atendimento, status de entrega operacional e status de corte/cancelamento individual por item.

---

## 1. Variáveis da Tela (`Var - F7`)

| Variável | Descrição / Label | Tipo de Componente | Obrigatório | Padrão / Instrução |
| :--- | :--- | :--- | :--- | :--- |
| `NR1` | Código Fornecedor | Numérico | Não | `0` (Zero para todos os fornecedores) |
| `DT1` | Data Inicial | Data | Sim | Data inicial de emissão do pedido |
| `DT2` | Data Final | Data | Sim | Data final de emissão do pedido |
| `DT3` | Data FINAL de entrega | Data | Não | Data limite máxima desejada para recebimento (deixar vazio para trazer todos) |
| `LS1` | Comprador | Lista de Seleção | Sim | Lista dinâmica de compradores com opção `'TODOS'` |
| `LS2` | Status Entrega | Lista de Seleção | Sim | Lista de status de entrega (`TODOS`, `TOT_ATEND`, `ATEND_PARC`, etc.) |

---

## 2. SQLs das Listas de Seleção (`LSx`)

### `LS1` - Lista de Compradores
```sql
SELECT 'TODOS' FROM DUAL UNION ALL SELECT TO_CHAR(SEQCOMPRADOR) || ' - ' || NVL(APELIDO, COMPRADOR) FROM MAX_COMPRADOR WHERE STATUS = 'A'
```

### `LS2` - Lista de Status de Entrega (127 caracteres)
```sql
SELECT DECODE(LEVEL,1,'TODOS',2,'TOT_ATEND',3,'ATEND_PARC',4,'NÃO_ATENDIDO',5,'ATRASO',6,'AGUARDANDO') FROM DUAL CONNECT BY LEVEL<=6
```

---

## 3. Passo a Passo Operacional

1. No Totvs Consinco, abra a tela **Consulta Criação**.
2. Cole a query contida em `Aplicativos/gerenciamento_sql/querys/consulta_pedidos_pendentes_fornecedor_cd.sql`.
3. Pressione a tecla **F7** (ou clique no botão `Var`).
4. Cadastre cada uma das variáveis acima (`NR1`, `DT1`, `DT2`, `DT3`, `LS1`, `LS2`).
5. Nas variáveis de lista (`LS1` e `LS2`), cole os respectivos SQLs no campo de instrução da lista.
6. Salve a configuração e execute a consulta.
