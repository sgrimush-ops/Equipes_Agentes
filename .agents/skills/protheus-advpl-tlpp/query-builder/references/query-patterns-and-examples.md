# Query Patterns and Code Examples

Complete AdvPL/TLPP code templates for each Protheus query pattern. Use these as starting points and adapt to the specific table, fields, and business logic.

---

## Pattern 1: Simple Select with Workarea

Use **Workarea access** when:

- Navegando registros sequencialmente por índice existente
- Operações registro a registro (lock, update)
- A tabela tem índice adequado para o padrão de acesso

```tlpp
#include "tlpp-core.th"
#include "totvs.ch"

Static Function GetCustomerName(cCustCode as Character) as Character
  Local cName := "" as Character
  Local aArea := SA1->(GetArea()) as Array

  DbSelectArea("SA1")
  SA1->(DbSetOrder(1))  // Index 1: A1_FILIAL + A1_COD + A1_LOJA

  If SA1->(DbSeek(FWxFilial("SA1") + cCustCode))
    cName := AllTrim(SA1->A1_NOME)
  EndIf

  SA1->(RestArea(aArea))
Return cName
```

---

## Pattern 2: Simple Select with Embedded SQL (FWExecStatement)

> **Prefira `FWExecStatement` ao invés do macro legado `TCQuery cQuery New Alias ...`.** `FWExecStatement` oferece bind de parâmetros no DB, cache de query e previne SQL injection.

Use **Embedded SQL** quando:

- Realizando joins complexos
- Usando agregações (SUM, COUNT, etc.)
- Query não mapeia para um único índice
- Leitura de grandes volumes de dados

```tlpp
#include "tlpp-core.th"
#include "totvs.ch"

Static Function GetCustomerBalance(cCustCode as Character) as Numeric
  Local nBalance := 0 as Numeric
  Local cQuery   := "" as Character
  Local oStatement := Nil as Object

  cQuery := "SELECT SUM(E1_SALDO) AS BALANCE " + ;
    "FROM " + RetSQLName("SE1") + " SE1 " + ;
    "WHERE SE1.D_E_L_E_T_ = ? " + ;
    "AND SE1.E1_FILIAL = ? " + ;
    "AND SE1.E1_CLIENTE = ? " + ;