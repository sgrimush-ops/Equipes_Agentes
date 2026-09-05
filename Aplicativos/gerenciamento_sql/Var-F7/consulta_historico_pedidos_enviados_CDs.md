# Var-F7 - Consulta Histórico de Pedidos Enviados aos CDs

## Query Vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_historico_pedidos_enviados_CDs.sql`

## Objetivo
Consultar o ciclo de vida completo dos pedidos de suprimento/transferência emitidos pelas lojas para os CDs, rastreando:
- Número do pedido e loja de destino
- Usuário de digitação (`USUINCLUSAO`) e data/hora do envio (`DTAHORINCLUSAO`)
- Informações do fornecedor (`MAP_FAMFORNEC`) e produto
- Quantidades solicitadas, canceladas/cortadas no CD, expedidas pelo CD, em trânsito e recebidas na loja
- Status de atendimento calculado e ofertas promocionais vigentes no período
- Saldo atual e data da última compra do item no estoque do CD

---

## Variáveis para Cadastrar em Var - F7

| Variável | Tipo | Tipo de Retorno | Descrição | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|---|
| **`DT1`** | Data | - | Data Inicial Emissão | - | Data de emissão inicial do pedido |
| **`DT2`** | Data | - | Data Final Emissão | - | Data de emissão final do pedido |
| **`LT1`** | Literal | Literal | Lojas Destino | `TODOS` | Digite os códigos das lojas separados por vírgula (ex: `1, 2, 11`) ou `TODOS` / `0` |
| **`LT2`** | Literal | Literal | Fornecedores | `TODOS` | Digite os códigos dos fornecedores separados por vírgula (ex: `1001, 2002, 3003`) ou `TODOS` / `0` |
| **`NR1`** | Numérico | - | Código Produto | `0` | Informe o código do produto (`SEQPRODUTO`) ou deixe `0` para trazer todos |
| **`LS1`** | Lista | Literal | Status Atendimento | `TODOS` | Selecione o status desejado ou escolha `TODOS` |

---

## SQL da Lista LS1 (Status Atendimento)
Cole o script SQL abaixo no cadastro da variável `LS1` dentro de **Var - F7** (limite de 145 caracteres):

```sql
SELECT 'TODOS' FROM DUAL UNION ALL SELECT 'ATENDIDO TOTAL' FROM DUAL UNION ALL SELECT 'EM TRANSITO' FROM DUAL UNION ALL SELECT 'EM SEPARACAO CD' FROM DUAL
```

---

## Passo a Passo Operacional no Totvs Consinco

1. Abra a tela **Consulta Criação** no Totvs Consinco.
2. Cole o código SQL do arquivo `consulta_historico_pedidos_enviados_CDs.sql`.
3. Pressione a tecla **Var - F7**.
4. Configure as variáveis:
   - **`DT1` e `DT2`** na aba **Data**.
   - **`LT1` e `LT2`** na aba **Literal** com valor padrão `TODOS`.
   - **`NR1`** na aba **Numérico** com valor padrão `0`.
   - **`LS1`** na aba **Lista** com o SQL da lista acima.
5. Salve e execute a consulta.
