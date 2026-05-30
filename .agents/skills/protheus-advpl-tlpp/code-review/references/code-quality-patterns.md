# Code Quality Patterns — Performance, Legacy, Metadata, Compilation

Exemplos detalhados para revisão de performance, legados, acesso a metadados e compilação.

---

## Performance e Loops

### APIs proibidas em loops

```advpl
// RUIM: GetMV dentro do loop
While !Eof()
  cParam := GetMV("MV_ESTADO")
  dbSkip()
EndDo

// BOM: Cache antes do loop
Local cParam := GetMV("MV_ESTADO")
While !Eof()
  dbSkip()
EndDo
```

**Proibidas em loops:** GetMV(), SuperGetMV(), ExistBlock(), AllUsers(), Type(), Pergunte()

### APIs de UI em transações

```advpl
// RUIM: MsgAlert dentro de transação
Begin Transaction
  If lError
    MsgAlert("Erro!")
  EndIf
End Transaction

// BOM: Coleta erro, mostra UI depois
Local cError := ""
Begin Transaction
  If lError
    cError := "Erro"
    DisarmTransaction()
  EndIf
End Transaction
If !Empty(cError)
  MsgAlert(cError)
EndIf
```

**Proibidas em transação:** MsgAlert(), MsgYesNo(), MsgInfo(), Aviso(), Help(), Pergunte(), ParamBox()
