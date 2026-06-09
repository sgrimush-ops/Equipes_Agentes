# Var-F7 — consulta_faturamento

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_faturamento.sql`

## Objetivo
Consultar o total global de compras faturadas por fornecedor dentro de um determinado período (agrupado por fornecedor/CNPJ), filtrando pelos CGOs de compra (1, 28, 32, 200, 290).

---

## Variáveis para cadastrar em Var-F7

### DT1 — Data Inicial
| Campo         | Valor                                    |
|---------------|------------------------------------------|
| Nome          | DT1                                      |
| Tipo          | Data                                     |
| Descrição     | Data inicial do período de entrada       |
| Valor Padrão  | (Vazio - preencher ao executar)          |

### DT2 — Data Final
| Campo         | Valor                                    |
|---------------|------------------------------------------|
| Nome          | DT2                                      |
| Tipo          | Data                                     |
| Descrição     | Data final do período de entrada         |
| Valor Padrão  | (Vazio - preencher ao executar)          |

---

## Passo a Passo — Cadastro em Var-F7

1. Abra a **Consulta Criação** no Consinco e localize ou crie a consulta `consulta_faturamento`.
2. Acesse **Var-F7** (botão ou tecla F7 na tela de cadastro de consulta).
3. Cadastre **DT1**:
   - Tipo: `Data`
   - Descrição: `Data inicial do período de entrada`
4. Cadastre **DT2**:
   - Tipo: `Data`
   - Descrição: `Data final do período de entrada`
5. Salve as variáveis.
6. Carregue o código SQL do arquivo `consulta_faturamento.sql` no editor da consulta e clique em salvar.
7. Ao clicar em executar (Run), informe o período desejado nas variáveis `DT1` e `DT2` apresentadas.

---

## Observações

- **CGOs de compra contemplados:** Fixo no SQL via `CODGERALOPER IN (1, 28, 32, 200, 290)`.
- **Status das Notas:** Filtro automático `STATUSNF <> 'C'` para desconsiderar notas fiscais canceladas.
- **Formatação de CNPJ:** Utiliza a função interna da Consinco `FC5MASKCNPJCPF` para exibir o CNPJ formatado no padrão com pontos, barras e traço.
- **Resolução de Valores Zerados (Faturamento por Item)**: A tabela de cabeçalho (`MLF_NOTAFISCAL`) foi vinculada à de itens (`MLF_NFITEM`) para somar a coluna `VLRTOTALITEM`, garantindo que os valores de faturamento sejam extraídos e somados corretamente a partir dos itens de cada nota.
