# FWRest Client Code Templates

Helpers e templates para integrações REST.

---

## Helpers compartilhados

```tlpp
#include "tlpp-core.th"
#include "totvs.ch"

Namespace empresa.integracao.rest

Static Function BuildJsonHeader(cAuth as Character) as Array
  Local aHeader := {} as Array
  aAdd(aHeader, "Content-Type: application/json")
  aAdd(aHeader, "Accept: application/json")
  If !Empty(cAuth)
    aAdd(aHeader, "Authorization: " + cAuth)
  EndIf
Return aHeader

Static Function LogRestError(cTag as Character, cUrl as Character, cHttpCode as Character, cError as Character, cBody as Character)
  Local cMsg := cTag + " | URL=" + cUrl + " | HTTP=" + cHttpCode + " | ERR=" + cError as Character
  If !Empty(cBody)
    cMsg += " | BODY=" + SubStr(cBody, 1, 500)
  EndIf
  FWLogMsg("ERROR", , "REST_CLIENT", FunName(), , "01", cMsg, 0, 0, {})
Return Nil
```

## GET com parâmetros

```tlpp
#include "tlpp-core.th"
#include "totvs.ch"

Namespace empresa.integracao.crm

User Function CrmListCustomers(nPage as Numeric, nPageSize as Numeric) as Json
  Local oClient   := Nil as Object
  Local aHeader   := {} as Array
  Local cQuery    := "" as Character
  Local cResponse := "" as Character
  Local cHttpCode := "" as Character