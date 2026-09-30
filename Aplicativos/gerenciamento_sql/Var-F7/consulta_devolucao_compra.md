# Var-F7 - Consulta de Devolucao de Compra com Filtro de Rede

## Objetivo
Listar uma linha por nota fiscal de devolucao de compra com loja, numero da NF, rede, codigo e razao social do fornecedor, valores, observacao/motivo da devolucao e as listas de codigos e descricoes dos produtos, permitindo filtrar por fornecedor, período de emissao e Rede (`LS1`).

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_devolucao_compra.sql`

## Variaveis para cadastrar em Var - F7

| Variavel | Tipo | Descricao | Valor padrao | Instrucao ao Usuario |
|---|---|---|---|---|
| `NR1` | Numerico | Codigo do fornecedor (`SEQPESSOA`) ou `0` para todos | `0` | Digite o codigo do fornecedor ou `0` para todos |
| `DT1` | Data | Data inicial de emissao | - | Informe a data inicial |
| `DT2` | Data | Data final de emissao | - | Informe a data final |
| `LS1` | Lista | Rede do Fornecedor | ` TODAS AS REDES` | Selecione a Rede desejada ou deixe ` TODAS AS REDES` |

---

## SQL da Lista LS1 (Rede)
Cole o script SQL abaixo no cadastro da variavel `LS1` dentro de **Var - F7** (limite de 145 caracteres):

```sql
SELECT ' TODAS AS REDES' FROM DUAL UNION ALL SELECT DESCRICAO FROM GE_REDE
```

---

## Configuracao e Passo a Passo

1. Abra a tela **Consulta Criacao** no Totvs Consinco.
2. Pressione **Var - F7** para abrir a janela de parametros/variaveis.
3. Cadastre as variaveis `NR1`, `DT1`, `DT2` e `LS1` conforme a tabela acima.
4. No cadastro da variavel `LS1`, selecione o tipo **Lista** e cole o SQL da lista acima.
5. Salve e execute a consulta informando os parametros desejados.