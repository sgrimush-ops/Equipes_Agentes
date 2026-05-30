# Code Analysis Tools — Protheus

Ferramentas e padrões para busca e análise estrutural em AdvPL/TLPP.

## Prioridade
1. ripgrep (rg) — busca rápida com contexto
2. grep — fallback universal

## Exemplos
- Encontrar User/Static Function:
  - rg '^(User |Static )?Function\s+\w+' --include="*.prw" --include="*.tlpp" --include="*.prg"
  - grep -rn "^User Function\s\|^Static Function\s" --include="*.prw" --include="*.tlpp" --include="*.prg"
- Encontrar classes TLPP:
  - rg '^class\s+\w+' --include="*.tlpp"
- Encontrar chamadas de método:
  - rg '::\w+\(' --include="*.tlpp" -l
- Encontrar padrões MVC:
  - rg '^(Static )?Function\s+(ModelDef|ViewDef|MenuDef|BrowseDef)' --include="*.prw" --include="*.tlpp"