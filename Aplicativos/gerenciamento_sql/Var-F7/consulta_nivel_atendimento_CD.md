# Var-F7 - Consulta Nível de Atendimento CD (com Local de Apanha WMS)

## Query Vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_nivel_atendimento_CD.sql`

## Objetivo
Consolidar por produto o nível de atendimento dos pedidos de suprimento emitidos pelas lojas para os CDs no período informado, exibindo:
- Código e Descrição do Produto
- **Local de Apanha no WMS (`LOCAL_APANHA`)** extraído de `MLO_ENDERECO` (`ESPECIEENDERECO = 'A'`), ou `'SEM APANHA'` caso não exista
- Estoque disponível atual no CD
- Total de pedidos e contagem de ocorrências por status (`ATENDIDO TOTAL`, `ATENDIDO PARCIAL`, `CORTADO/CANCELADO`, `EM TRANSITO`, `EM SEPARACAO CD`, `NAO ATENDIDO`)
- Quantidade de NFs emitidas, volume total solicitado vs. expedido e data da última expedição

---

## Variáveis para Cadastrar em Var - F7

| Variável | Tipo | Tipo de Retorno | Descrição | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|---|
| **`DT1`** | Data | - | Data Inicial Emissão | - | Data de emissão inicial do pedido |
| **`DT2`** | Data | - | Data Final Emissão | - | Data de emissão final do pedido |
| **`LT1`** | Literal | Literal | Lojas Destino | `TODOS` | Digite os códigos das lojas separados por vírgula (ex: `1, 2, 11`) ou `TODOS` / `0` |
| **`LT2`** | Literal | Literal | CD Origem | `15` | Digite os códigos dos CDs de origem separados por vírgula (ex: `15, 16`) ou `TODOS` |
| **`NR1`** | Numérico | - | Código Produto | `0` | Informe o código do produto (`SEQPRODUTO`) ou deixe `0` para trazer todos |
| **`LS1`** | Lista | Literal | Status Atendimento | `TODOS` | Selecione o status desejado ou escolha `TODOS` |

---

## SQL da Lista LS1 (Status Atendimento)
Cole a instrução SQL abaixo (125 caracteres, respeitando o limite de 145 caracteres e prevenindo truncamento Delphi via `DECODE` + `CONNECT BY`) no cadastro da variável `LS1` em **Var - F7**:

```sql
SELECT DECODE(LEVEL,1,'TODOS',2,'ATENDIDO TOTAL',3,'ATENDIDO PARCIAL',4,'CANCELADO',5,'CORTADO NF',6,'EM TRANSITO',7,'EM SEPARACAO CD') FROM DUAL CONNECT BY LEVEL<=7
```
*(Alternativa com constantes literais diretas no campo de lista: `TODOS;ATENDIDO TOTAL;ATENDIDO PARCIAL;CANCELADO;CORTADO NF;EM TRANSITO;EM SEPARACAO CD;NAO ATENDIDO`)*

---

## Passo a Passo Operacional no Totvs Consinco

1. Abra a tela **Consulta Criação** no Totvs Consinco.
2. Cole o código SQL do arquivo `consulta_nivel_atendimento_CD.sql`.
3. Pressione o botão **Var - F7**.
4. Cadastre as variáveis `DT1`, `DT2`, `LT1`, `LT2`, `NR1` e `LS1` conforme a tabela acima.
5. Salve e clique em **Executar (Run / F8)**.

