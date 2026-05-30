# Security Review Patterns (SonarQube G1)

Exemplos detalhados para achados de revisão de segurança.

---

## SQL Injection (CA2050 / CA2051) — CRÍTICO

```advpl
// RUIM: Concatenando input do usuário em SQL
cQuery := "SELECT * FROM " + RetSqlName("SA1") + " WHERE A1_COD = '" + cCodCli + "'"
dbSelectArea("SA1")
dbSetQuery(cQuery)

// BOM: Use FWExecStatement para evitar injection
Local cQuery   := "SELECT A1_COD, A1_NOME FROM " + RetSqlName("SA1") + ;
                  " WHERE D_E_L_E_T_ = ? AND A1_FILIAL = ? AND A1_COD = ?" as Character
Local oStatement := FWExecStatement():New(ChangeQuery(cQuery)) as Object
Local cAlias as Character

oStatement:SetString(1, ' ')
oStatement:SetString(2, FWxFilial("SA1"))
oStatement:SetString(3, cCodCli)

cAlias := oStatement:OpenAlias()    // executa com bind no DB
// ... consumir (cAlias)->A1_COD / A1_NOME ...
(cAlias)->(DBCloseArea())
oStatement:Destroy()
```

> `FWExecStatement` (lib `20211116`+) estende `FWPreparedStatement` e adiciona cache de query. Use `:ExecScalar(cColumn)` para SELECT de valor único e `TCSqlExec(:GetFixQuery())` para DML. Nunca use `:SetUnsafe()` com input do usuário.

---

## Hardcoded Credentials (CA2052) — CRÍTICO

```advpl
// RUIM: Senha exposta no código
cPassword := "admin123"

// BOM: Use configuração de ambiente
cPassword := GetMV("XX_SRVPASS")
```

---

## Contexto de ambiente em REST/SOAP (BG1000) — MAJOR

```advpl
// RUIM: RpcSetEnv manual em serviço REST
@Get("/api/customers")
User Function GetCust()
  RpcSetEnv("T1", "M SP 01")  // Proibido em REST
  // ...
Return

// BOM: Configure PrepareIn no REST Server
// appserver.ini: [HTTPREST] > PrepareIn=T1,M SP 01
```