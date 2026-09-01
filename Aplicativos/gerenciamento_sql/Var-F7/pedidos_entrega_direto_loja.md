# Var-F7 - pedidos_entrega_direto_loja

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/pedidos_entrega_direto_loja.sql`

## Objetivo
Consultar pedidos de compra para **entrega direto em loja** (excluindo os Centros de Distribuição 15, 16 e 50), trazendo informações detalhadas por item: 
- Comprador
- Fornecedor
- Número do Pedido
- Loja Destino
- Data de Emissão (`DATA_EMISSAO`)
- Data de Previsão de Entrega (`DATA_PREV_ENTREGA`)
- Data Limite de Entrega (`DATA_LIMITE_ENTREGA`)
- Código e Descrição do Produto
- Quantidade da Embalagem de Compra (`QTD_EMBALAGEM`)
- Quantidade Pedida (`QUANTIDADE_PEDIDA`) em caixas/embalagens
- Quantidade Atendida (`QUANTIDADE_ATENDIDA`) em caixas/embalagens
- Percentual de Atendimento (`PERC_ATENDIMENTO`)
- Apuração do Status de Entrega (`STATUS_ENTREGA`)
- Status do Pedido (`STATUS_PEDIDO`)

### Lógica da Coluna STATUS_ENTREGA:
1. **`TOT_ATEND`**: Quando o `PERC_ATENDIMENTO` atingir `100%` (ou quantidade atendida >= quantidade pedida).
2. **Quando `PERC_ATENDIMENTO < 100%`**:
   - **`NÃO_.ATENDIDO`**: Se a data limite de entrega (`DTALIMITERECEBTO`) já passou da data de hoje (`< SYSDATE`).
   - **`ATRASO`**: Se a data de previsão de entrega (`DTARECEBTO`) já passou da data de hoje (`< SYSDATE`), mas ainda não ultrapassou o limite.
   - **`AGUARDANDO`**: Se a data prevista de entrega ainda está vigente (`>= SYSDATE`).

## Variáveis para cadastrar em Var - F7

| Variável | Tipo | Tipo de Retorno | Descrição | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|---|
| **DT1** | Data | - | Data Inicial Emissão | - | Informe a data inicial de emissão dos pedidos. |
| **DT2** | Data | - | Data Final Emissão | - | Informe a data final de emissão dos pedidos. |
| **LS1** | Lista | Literal | Comprador | TODOS | Selecione o apelido do comprador ou escolha `TODOS`. |
| **NR1** | Numérico | - | Código Fornecedor | 0 | Informe o código da pessoa/fornecedor (`SEQFORNECEDOR`) ou deixe `0` para todos. |

---

## SQL da Lista LS1 (Comprador)
Cole o script SQL abaixo no cadastro da variável `LS1` dentro de **Var - F7** (respeitando o limite de 145 caracteres):

```sql
SELECT 'TODOS' AS APELIDO FROM DUAL UNION ALL SELECT DISTINCT NVL(APELIDO, COMPRADOR) FROM MAX_COMPRADOR WHERE APELIDO IS NOT NULL
```

*(Ou, caso prefira o formato numérico `0 - TODOS` / `Código - Apelido`):*
```sql
SELECT '0 - TODOS' FROM DUAL UNION ALL SELECT TO_CHAR(SEQCOMPRADOR)||' - '||NVL(APELIDO,COMPRADOR) FROM MAX_COMPRADOR WHERE SEQCOMPRADOR>0
```

---

## Passo a Passo Operacional no Totvs Consinco

1. Acesse o módulo **Consulta Criação** no Totvs Consinco.
2. Cole o conteúdo atualizado do script `pedidos_entrega_direto_loja.sql` na área de texto.
3. Pressione a tecla de atalho **Var - F7** (ou clique no botão correspondente).
4. Na aba **Data**, cadastre as variáveis `:DT1` (Data Inicial) e `:DT2` (Data Final).
5. Na aba **Lista**, cadastre a variável `:LS1`:
   - Descrição: `Comprador`
   - Retorno: `Literal`
   - Valor Padrão: `TODOS` (ou `0 - TODOS`)
   - SQL da lista: Cole o script SQL da lista acima.
6. Na aba **Numérico**, cadastre a variável `:NR1`:
   - Descrição: `Código Fornecedor`
   - Valor Padrão: `0`
7. Clique em **Salvar / Confirmar** no formulário de variáveis.
8. Execute a consulta pressionando **F8 (Run)** e informe os filtros desejados.
