# Convenções de Código AdvPL/TLPP (Protheus)

## Estrutura de Projeto
- Fontes organizados por módulo (Financeiro, Compras, etc.)
- Sufixos de arquivo: .prw, .tlpp, .prg, .prx
- Testes automatizados em Python (TIR)
- Skills de agente em .agents/skills/

## Convenções de Nomenclatura
- Notação húngara obrigatória: c (char), n (num), l (log), a (array), o (obj), d (data), b (codeblock), x (variant), j (json)
- Arquivos: prefixo módulo (4 letras) + número (3 dígitos) — ex: MATA010
- Campos: prefixo tabela + _ + nome — ex: A1_COD
- Tabelas: alias de 2-3 letras — ex: SA1, SE1, SD1
- Constantes multilíngue: STR0001 a STR9999 em .ch

## Tipos AdvPL
- Character (C), Memo (M), Numeric (N), Logical (L), Date (D), Fixed Decimal (F), Array (A), Code Block (B), Undefined (U), Object (O)

## Tipos TLPP
- numeric, integer, double, string, logical, date, array, object

## Boas práticas
- Comentários e documentação em português
- Identificadores técnicos em inglês/padrão Protheus
- Sempre documentar funções/classes com ProtheusDOC
- Seguir padrões de modularização e separação de responsabilidades
