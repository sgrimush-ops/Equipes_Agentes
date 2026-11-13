# Var-F7 - Consulta de Devolucao de Compra com Filtro de Rede e NFs Referenciadas (`LT1`)

## Objetivo
Listar uma linha por nota fiscal de devolucao de compra (`CGO 802, 860`) com loja, numero da NF, rede, codigo e razao social do fornecedor/destinatario, valores, observacao/motivo da devolucao (onde constam as NFs de origem referenciadas) e as listas de codigos e descricoes dos produtos, permitindo filtrar por fornecedor (`NR1`), periodo de emissao (`DT1` e `DT2`), Rede (`LS1`) e multiplos numeros de NF separados por virgula (`LT1` — busca tanto na `OBSERVACAO` de NFs referenciadas quanto no proprio `NUMERONF` de devolucao).

## Query vinculada
- Arquivo SQL: `Aplicativos/gerenciamento_sql/querys/consulta_devolucao_compra.sql`

## Variaveis para cadastrar em Var - F7

| Variavel | Tipo | Descricao | Valor padrao | Instrucao ao Usuario |
|---|---|---|---|---|
| `NR1` | Numerico | Codigo do fornecedor/destinatario (`SEQPESSOA`) ou `0` para todos | `0` | Digite o codigo do fornecedor ou `0` para todos (use `0` se suspeitar que a devolucao foi emitida contra a transportadora) |
| `DT1` | Data | Data inicial de emissao da devolucao | - | Informe a data inicial (ex: `01/06/2026`) |
| `DT2` | Data | Data final de emissao da devolucao | - | Informe a data final |
| `LS1` | Lista | Rede do Fornecedor | ` TODAS AS REDES` | Selecione a Rede desejada ou deixe ` TODAS AS REDES` |
| `LT1` | Literal | NFs Referenciadas ou NFs de Devolucao (separadas por virgula) ou `0` para todas | `0` | Digite as NFs separadas por virgula (ex: `423533, 423534`) ou `0` para listar todas |

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
3. Cadastre/confira as variaveis `NR1`, `DT1`, `DT2`, `LS1` e inclua a nova variavel `LT1` do tipo **Literal** com valor padrao `0`.
4. No cadastro da variavel `LS1`, selecione o tipo **Lista** e cole o SQL da lista acima.
5. Para investigar as NFs `423533` e `423534` (inclusive caso tenham sido devolvidas contra a transportadora e nao contra o fornecedor `16491`):
   - `NR1`: `0` (importante deixar `0` para nao ocultar notas emitidas contra o `SEQPESSOA` da transportadora)
   - `DT1`: `01/06/2026` (data do recebimento em diante)
   - `DT2`: data final desejada
   - `LS1`: ` TODAS AS REDES`
   - `LT1`: `423533, 423534`
