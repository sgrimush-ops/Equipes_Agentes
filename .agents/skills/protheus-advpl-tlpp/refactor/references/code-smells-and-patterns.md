# Code Smells, Refactoring Techniques & Design Patterns

Exemplos antes/depois para refatoração e padrões.

---

## 1. Função longa

```diff
# RUIM: Função de 300 linhas
- User Function ProcPedido()
-   // ...
- Return

# BOM: Quebre em funções estáticas
+ User Function ProcPedido() as Logical
+   aPedido := BuscaPedido()
+   If !ValidaCliente(aPedido)
+     Return .F.
+   EndIf
+   nPreco := CalculaPreco(aPedido)
+   AtualizaEstoque(aPedido)
+   CriaRemessa(aPedido)
+   EnviaNotificacoes(aPedido, nPreco)
+   lOk := .T.
+ Return lOk

+ Static Function BuscaPedido() as Array
+   // busca SCR
+ Return aRes

+ Static Function ValidaCliente(aPedido as Array) as Logical
+   // valida SA1
+ Return lValido

+ Static Function CalculaPreco(aPedido as Array) as Numeric
+   // busca SB1, calcula desconto
+ Return nTotal
```

## 2. Código duplicado

```diff
# RUIM: Mesma lógica em vários lugares
- If x == 1
-   FazAlgo()
- ElseIf x == 2
-   FazAlgo()
- EndIf

# BOM: Extraia função
+ Static Function FazAlgo()
+   // lógica única
+ Return
```