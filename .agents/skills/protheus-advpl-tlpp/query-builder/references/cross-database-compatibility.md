# Cross-Database Compatibility

Protheus suporta PostgreSQL, MSSQL Server e Oracle. Todo SQL deve ser compatível ou usar as ferramentas abaixo.

---

## ChangeQuery() — Tradução de dialeto SQL

`ChangeQuery(cQuery)` traduz SQL para o dialeto do banco ativo antes de executar. Lida com diferenças de TOP/LIMIT, datas, strings.

```tlpp
// BOM: Use ChangeQuery() para compatibilidade cross-DB
Local cQuery     := "SELECT TOP 10 A1_COD, A1_NOME FROM " + RetSQLName("SA1") + " SA1 " + ;
                    "WHERE SA1.D_E_L_E_T_ = ? AND SA1.A1_FILIAL = ?"
Local oStatement := FWExecStatement():New(ChangeQuery(cQuery))
Local cAlias     as Character

oStatement:SetString(1, ' ')
oStatement:SetString(2, FWxFilial("SA1"))
cAlias := oStatement:OpenAlias()
// ... consumir (cAlias)->campos ...
(cAlias)->(DBCloseArea())
oStatement:Destroy()
```

> FWExecStatement é o preferido para SQL embarcado — chama ChangeQuery() e faz bind de parâmetros. O macro TCQuery e BeginSQL/EndSQL também chamam ChangeQuery(), mas não garantem bind seguro.

---

## TCGetDB() — Detecção de banco em runtime

Use TCGetDB() para lógica específica de banco:

```tlpp
Local cDB := TCGetDB()
Do Case
  Case cDB == "MSSQL"
    // Sintaxe MSSQL
  Case cDB == "ORACLE"
    // Sintaxe Oracle
  Case cDB == "POSTGRES"
    // Sintaxe PostgreSQL
EndCase
```

---

## Macros DBAccess

Macros para SQL e SQL embarcado. DBAccess traduz por banco:

| Macro         | Expansão                                              | Descrição                                         |
| ------------- | ----------------------------------------------------- | ------------------------------------------------- |
| `%nolock%`    | `WITH (NOLOCK)` no MSSQL; ignora nos outros           | Evita lock em leitura                             |
| `%notDel%`    | `D_E_L_E_T_ = ' '`                                   | Filtro soft-delete                                |
| `%table:XXX%` | `RetSqlName('XXX')`                                  | Nome físico da tabela                             |
| `%Order:XXX%` | `SqlOrder(XXX->(IndexKey()))`                        | Lista de colunas ordenadas por índice             |
