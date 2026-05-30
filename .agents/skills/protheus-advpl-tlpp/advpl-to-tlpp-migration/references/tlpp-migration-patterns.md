# TLPP Migration Patterns

Exemplos detalhados de migração AdvPL → TLPP.

## 1. Extensão e includes

Troque a extensão e atualize o include:

```diff
- // myfile.prw
- #include "protheus.ch"
+ // myfile.tlpp
+ #include "tlpp-core.th"
+ #include "totvs.ch"
```

> `totvs.ch` pode coexistir com `tlpp-core.th`. Remova só se não usar Protheus.

## 2. Namespace

Organize o código em namespaces lógicos:

```diff
+ #include "tlpp-core.th"
  #include "totvs.ch"

+ Namespace empresa.modulo.funcionalidade
+
  User Function MinhaRotina()
```

## 3. Tipagem

Adicione tipos em variáveis, parâmetros e retorno:

```diff
- User Function CalcTotal(cCodCli, nDesc)
-   Local cNome   := ""
-   Local nTotal  := 0
-   Local lOk     := .F.
-   Local dData   := CToD("")
-   Local aItens  := {}
-   Local oModel  := Nil
+ User Function CalcTotal(cCodCli as Character, nDesc as Numeric) as Numeric
+   Local cNome   := "" as Character
+   Local nTotal  := 0 as Numeric
+   Local lOk     := .F. as Logical
+   Local dData   := CToD("") as Date
+   Local aItens  := {} as Array
+   Local oModel  := Nil as Object
```

**Palavras-chave TLPP:**
| Tipo | Palavra-chave | Prefixo húngaro |