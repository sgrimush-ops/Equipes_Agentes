# Var-F7 - Comparativo de Estoque WMS vs ERP Comercial

## Query Vinculada
- Arquivo oficial (Consulta Criação): [comparativo_estoque_wms_vs_erp.sql](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/gerenciamento_sql/querys/comparativo_estoque_wms_vs_erp.sql)

---

## Estrutura das Colunas Abreviadas
| Coluna | Descrição |
|---|---|
| **`DEPTO`** | Departamento mercadológico oficial (1ª coluna) |
| **`CD`** | Código do CD/Empresa consultado |
| **`CODIGO`** | Código do Produto (`SEQPRODUTO`) |
| **`DESCRICAO`** | Descrição completa do produto |
| **`ERP_DISP`** | Estoque Disponível no ERP (`ESTQDEPOSITO`) |
| **`ERP_TROCA`** | Estoque Troca/Avaria no ERP (`ESTQTROCA`) |
| **`ERP_TOTAL`** | Estoque Total no ERP (`Depósito + Troca + Outros`) |
| **`WMS_APANHA`** | Estoque físico em Apanha/Picking (`ESPECIEENDERECO = 'A'`) |
| **`WMS_PULMAO`** | Estoque físico em Pulmão/Aéreo (`ESPECIEENDERECO = 'P'`) |
| **`WMS_OUTROS`** | Estoque físico em outros endereços WMS (Avaria/Trocas/Bloqueados) |
| **`WMS_REAL`** | Estoque operacional disponível no WMS (`Apanha + Pulmão` - sem trocas) |
| **`WMS_TOTAL`** | Estoque Total no WMS (`Apanha + Pulmão + Outros/Trocas`) |
| **`REC_PEND`** | Quantidade conferida em NF aguardando armazenagem |
| **`SEP_PEND`** | Quantidade reservada em separação de saída |
| **`DIF_BRUTA`** | Confronto Operacional: `ERP_DISP - WMS_REAL` |
| **`DIF_AJUST`** | Confronto com Trânsito: `ERP_DISP - (WMS_REAL + REC_PEND)` |
| **`STATUS`** | Diagnóstico operacional (`01 - ALINHADO`, `02 - EM RECEBIMENTO`, `03 - SOBRA ERP`, `04 - FALTA ERP`) |

---

## Variáveis para Cadastrar em Var - F7

### 1. `LT1` (Literal) — Empresas / CDs
| Campo | Valor |
|---|---|
| **Tipo** | Literal |
| **Descrição** | Empresas / CDs |
| **Valor Padrão** | `15` |
| **Instrução p/ Usuário** | Digite a empresa/CD ou múltiplos separados por vírgula (ex: `15` ou `15,16`). |

---

### 2. `NR1` (Numérico) — Código do Produto
| Campo | Valor |
|---|---|
| **Tipo** | Numérico |
| **Descrição** | Código do Produto (0 = Todos) |
| **Valor Padrão** | `0` |
| **Instrução p/ Usuário** | Digite o código do produto ou `0` para trazer todos. |

---

### 3. `LS1` (Lista) — Status do Comparativo
| Campo | Valor |
|---|---|
| **Tipo** | Lista |
| **Descrição** | Status do Comparativo |
| **Valor Padrão** | `TODOS` |
| **Instrução p/ Usuário** | Selecione o status de filtro desejado. |

#### Como Cadastrar a Variável LS1 (Escolha uma das opções):
- **Opção A (Constantes da Lista - Recomendada):** No campo da instrução, cole apenas o texto:
  `TODOS;ALINHADO;DIVERGENCIA;SOBRA ERP;SOBRA WMS;RECEBIMENTO`
- **Opção B (SQL com CAST explícito):**
  `SELECT CAST(COLUMN_VALUE AS VARCHAR2(50)) FROM TABLE(SYS.ODCIVARCHAR2LIST('TODOS','ALINHADO','DIVERGENCIA','SOBRA ERP','SOBRA WMS','RECEBIMENTO'))`

---

### 4. `LT2` (Literal) — Expurgos de Departamentos
| Campo | Valor |
|---|---|
| **Tipo** | Literal |
| **Descrição** | Expurgar Departamentos (separados por vírgula) |
| **Valor Padrão** | `almoxarifado, nao alimento, servico` *(ou `0` para não expurgar nada)* |
| **Instrução p/ Usuário** | Informe os nomes ou termos de departamentos a desconsiderar (ex: `almoxarifado, nao alimento, servico`). O filtro é imune a maiúsculas, minúsculas, espaços e acentos. Para desativar o expurgo, informe `0`. |

---

## Opções Disponíveis na Lista LS1:
- **`TODOS`**: Retorna todos os produtos cadastrados com saldo no ERP ou WMS.
- **`ALINHADO`**: Retorna exclusivamente produtos onde o estoque ERP está 100% igual ao WMS (`DIF_BRUTA = 0`).
- **`DIVERGENCIA`**: Apenas produtos onde o Estoque Comercial ERP difere do Estoque WMS (`DIF_BRUTA != 0`).
- **`SOBRA ERP`**: Produtos onde o Estoque ERP está maior que o físico no WMS (falta no estoque físico).
- **`SOBRA WMS`**: Produtos onde o WMS possui mais saldo físico do que o ERP (sobra no estoque físico).
- **`RECEBIMENTO`**: Produtos com cargas em recebimento pendentes de armazenagem no WMS.
