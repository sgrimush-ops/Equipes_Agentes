# Procedimento: Consulta Pedidos Pendentes Carga até NF

**Arquivo Query:** `consulta_ped_pendentes_carga_ate_nf.sql`  
**Data de Criação:** 14/05/2026  
**Status:** Homologação

## Resumo da Consulta

Expande a consulta original de pedidos pendentes de carga para incluir o **ciclo completo** desde o pedido de suprimento até a nota fiscal gerada. Mostra:

1. **Pedido de Suprimento** - Data, número, quantidade solicitada
2. **Pedido de Venda** - Ligação com o pedido de venda
3. **Separação** - Dados de carga, quantidade separada
4. **Conferência** - Data e usuário de conferência  
5. **NF** - Número, série, data, status, quantidade e valor da NF gerada
6. **Status do Ciclo** - Indicador visual do estágio atual (Pedido → Pedido Venda → Separação → NF)

## Variáveis de Filtro (Var-F7)

| Var | Tipo | Descricao | Sentinela | Exemplo |
|-----|------|-----------|-----------|---------|
| **DT1** | Data | Data inicial do período | (obrigatória) | 01/05/2026 |
| **DT2** | Data | Data final do período | (obrigatória) | 14/05/2026 |
| **LT1** | Literal | Departamento (filtro opcional) | TODOS | BEBIDAS |
| **LT2** | Literal | Código da loja destino (filtro opcional) | TODOS | 001 |
| **NR1** | Numérico | Código do produto (filtro opcional) | 0 | 860 |

## Colunas do Resultado

### Identificação do Item
- `CODIGO_EMPRESA` - Empresa de destino
- `CODIGO_PRODUTO` - Código interno do produto (SEQPRODUTO)
- `DESCRICAO_PRODUTO` - Descrição completa do produto
- `DEPARTAMENTO` - Categoria/Departamento (nível 1)

### Pedido de Suprimento
- `NRO_PEDIDO_SUPRIMENTO` - Número do pedido de suprimento
- `DATA_PEDIDO_SUPRIMENTO` - Data de emissão do pedido

### Informações de Estoque
- `ESTOQUE_DISPONIVEL_CD` - Estoque no CD (empresa 15)
- `ESTOQUE_DISPONIVEL_LOJA` - Estoque na loja destino

### Pedido de Venda e Separação
- `NRO_PED_VENDA` - Número do pedido de venda gerado
- `NROCARGA` - Número da carga
- `EMBALAGEM` - Unidade de embalagem
- `QUANTIDADE_A_EXPEDIR` - Quantidade planejada para expedir
- `QTD_SEPARADA` - Quantidade que foi separada
- `SALDO_A_SEPARAR` - Saldo ainda pendente de separação
- `QTD_CONFERIDA` - Quantidade que foi conferida
- `SALDO_A_CONFERIR` - Saldo ainda pendente de conferência

### Conferência
- `DATA_CONFERENCIA` - Data de conclusão da conferência
- `USUARIO_CONFERENCIA` - Usuário que realizou a conferência

### Status
- `ETAPA_ATUAL` - Estágio operacional atual (Cancelado, Aguardando Pedido Venda, Pedido Venda Criado, Aguardando Separacao, Separado - Sem Conferencia, Conferencia Parcial, Conferido)

## Alterações em Relação à Query Original

1. **Colunas operacionais novas**
   - `SALDO_A_SEPARAR`, `SALDO_A_CONFERIR`, `ETAPA_ATUAL`

2. **Coluna de status operacional**
   - Identifica automaticamente em qual etapa o item está dentro do fluxo de separação/conferência

3. **Ordenação**
   - Mantida por data, empresa e pedido de suprimento

## Passo a Passo de Cadastro da Consulta Criação

### Tela 1: Consulta
1. Abra **Consulta Criação** (MAX0151 ou F7)
2. Clique em **Novo**
3. Preencha:
   - **Nome:** `Pedidos Pendentes Carga até NF`
   - **Descrição:** `Ciclo completo de pedidos de suprimento até emissão de NF`
   - **Tipo de Banco:** Oracle
   - **Empresa:** 15

### Tela 2: SQL Principal
1. Cole todo o SQL de `consulta_ped_pendentes_carga_ate_nf.sql`
2. Mantenha as variáveis: `:DT1`, `:DT2`, `:LT1`, `:LT2`, `:NR1`
3. **Importante:** Manter `:NR1` como `NVL(:NR1, 0)` para permitir busca opcional por produto

### Tela 3: Variáveis (Var-F7)

Cadastre as 5 variáveis conforme tabela abaixo:

#### Variável DT1 (Data Inicial)
- **Nome:** DT1
- **Tipo:** Data
- **Obrigatória:** Sim
- **Valor Padrão:** (vazio)
- **Label:** Data Inicial

#### Variável DT2 (Data Final)
- **Nome:** DT2
- **Tipo:** Data
- **Obrigatória:** Sim
- **Valor Padrão:** (vazio)
- **Label:** Data Final

#### Variável LT1 (Departamento)
- **Nome:** LT1
- **Tipo:** Literal
- **Obrigatória:** Não
- **Valor Padrão:** TODOS
- **Label:** Departamento
- **Observação:** Use literal, não lista. Sentinela = TODOS

#### Variável LT2 (Loja Destino)
- **Nome:** LT2
- **Tipo:** Literal
- **Obrigatória:** Não
- **Valor Padrão:** TODOS
- **Label:** Loja Destino (Código)
- **Observação:** Sentinela = TODOS, aceita apenas código

#### Variável NR1 (Código Produto)
- **Nome:** NR1
- **Tipo:** Numérico
- **Obrigatória:** Não
- **Valor Padrão:** 0
- **Label:** Código Produto
- **Observação:** Sentinela = 0, deixar em branco para ver todos

## Notas Técnicas

### Pontos de Atenção
1. **Joins de NF podem retornar múltiplas linhas** - Um item pode estar em múltiplas NFs se houver devolução/complemento. O GROUP BY foi estruturado para evitar duplicatas, mas verificar resultado.

2. **Separação e conferência podem ficar zeradas** - isso não significa erro; a coluna `ETAPA_ATUAL` foi ajustada para mostrar melhor o estágio operacional real.

3. **Conferência por USUÁRIO** - Usa `MAX(...) KEEP (DENSE_RANK LAST ORDER BY ...)` para retornar o usuário da última tarefa de conferência, não a primeira.

### Possíveis Evoluções
- Adicionar filtro de status de NF (Normal/Cancelada)
- Adicionar filtro por range de valor de NF
- Incluir frete/seguros caso necessário
- Rastrear devoluções/complementos de NF

## Regras de Homologação Aplicadas

✓ Sentinelas explícitas (TODOS para texto, 0 para código)  
✓ Usar LT (literal) em vez de LS (lista) para departamento (conforme histórico homologado)  
✓ Manter estrutura de filtro padronizada (DT + DT + LT + LT + NR)  
✓ GROUP BY/ORDER BY alinhado com TRUNC de datas  
✓ LEFT JOIN para não perder dados de pedidos em fase intermediária  
✓ Status visual (CASE WHEN) para facilitar leitura do ciclo

