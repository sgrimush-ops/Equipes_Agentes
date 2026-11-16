# Var-F7 - Consulta de Boletos Emitidos (`MRL_TITULOFIN`)

## Query Vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_boletos_emitidos.sql`

## Objetivo
Listar todos os boletos efetivamente emitidos (`MRL_TITULOFIN.TITULOEMITIDO LIKE 'S%'`, `ESPECIEFORMAPAGTO = 'B'`, `OBRIGDIREITO = 'D'`), validando os parâmetros bancários de emissão (`MRL_PARAMCOBRANCA`) e expurgando notas fiscais canceladas (`MFL_DOCTOFISCAL.STATUSDF = 'C'`), com filtros antes do Run para Fornecedor (`NR1`), Lojas Emitentes separadas por vírgula (`LT1`), Números de NF/Documento separados por vírgula (`LT2`) e Período de Emissão (`DT1` a `DT2`).

---

## Variáveis para Cadastrar em Var - F7

| Variável | Tipo | Descrição | Valor Padrão | Instrução ao Usuário |
|---|---|---|---|---|
| **`NR1`** | Numérico | Código do Fornecedor | `0` | Digite o código do fornecedor (`SEQPESSOA`) ou deixe `0` para listar todos |
| **`LT1`** | Literal | Lojas Emitentes (vírgula) | `0` | Digite as lojas emitentes separadas por vírgula (ex: `15, 16, 3`) ou `0` para todas |
| **`LT2`** | Literal | NFs / Documentos (vírgula) | `0` | Digite os números das NFs separados por vírgula (ex: `91014, 91021`) ou `0` para todos |
| **`DT1`** | Data | Data Inicial de Emissão | - | Informe a data inicial de emissão do boleto |
| **`DT2`** | Data | Data Final de Emissão | - | Informe a data final de emissão do boleto |

---

## Passo a Passo Operacional de Configuração (`Var - F7`)

1. Abra o módulo **Consulta Criação** no Totvs Consinco.
2. Cole o código SQL principal na aba de comando.
3. Clique no botão **Var - F7** (ou pressione `F7`) para abrir o cadastro de variáveis de tela (os filtros visuais só aparecem se forem cadastrados manualmente em `Var - F7`).
4. Cadastre as **5 variáveis** abaixo:
   - **`NR1`**: Tipo **Numérico** | Descrição: `Codigo do Fornecedor (0=Todos)` | Valor Padrão: `0`
   - **`LT1`**: Tipo **Literal** | Descrição: `Lojas Emitentes sep. por virgula (0=Todas)` | Valor Padrão: `0`
   - **`LT2`**: Tipo **Literal** | Descrição: `NFs / Docs sep. por virgula (0=Todas)` | Valor Padrão: `0`
   - **`DT1`**: Tipo **Data** | Descrição: `Data Inicial de Emissao`
   - **`DT2`**: Tipo **Data** | Descrição: `Data Final de Emissao`
5. Salve o cadastro de variáveis e clique em **Run (F8)** para executar a consulta.
