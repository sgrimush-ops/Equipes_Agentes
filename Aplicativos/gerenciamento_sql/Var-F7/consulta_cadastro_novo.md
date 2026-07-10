# consulta_cadastro_novo — Cadastros Novos com Mínimo Baixo

## Objetivo
Listar produtos recém-cadastrados (dentro de X dias) que ainda possuem estoque mínimo abaixo de determinado valor. Útil para identificar itens novos que ainda não tiveram o mínimo parametrizado.

## Arquivo SQL
`Aplicativos/gerenciamento_sql/querys/consulta_cadastro_novo.sql`

---

## Variáveis — Var - F7

### :LS1 — Departamento
- **Tipo:** Lista
- **Descrição:** Filtro por departamento (categoria nível 1). Selecione no dropdown ou deixe `TODOS` para trazer todos.
- **Tipo de retorno:** Literal
- **Valor padrão:** TODOS
- **Instrução:** Selecione o departamento desejado na lista ou mantenha `TODOS`.

### :NR1 — Dias desde o cadastro
- **Tipo:** Numérico
- **Descrição:** Quantidade de dias atrás a partir de hoje. Traz somente produtos cadastrados DENTRO desse intervalo.
- **Valor padrão:** 30
- **Instrução:** Informe quantos dias quer olhar para trás. Ex.: `30` traz produtos cadastrados nos últimos 30 dias. Digite `0` caso queira ver produtos de qualquer data.

### :NR2 — Mínimo máximo aceito
- **Tipo:** Numérico
- **Descrição:** Filtra produtos onde ESTQMINIMOLOJA seja menor que este valor.
- **Valor padrão:** 1
- **Instrução:** Padrão `1` retorna itens com mínimo = 0 (mínimo não parametrizado). Digite `0` caso queira ignorar o filtro de estoque mínimo e ver todos os itens.

---

## SQL da lista LS1
Cole esta instrução SQL dentro do quadro da variável LS1 na tela Var - F7:

```sql
SELECT 'TODOS'
FROM DUAL
UNION
SELECT DISTINCT A.CATEGORIA
FROM MAP_CATEGORIA A
WHERE A.STATUSCATEGOR = 'A'
  AND A.TIPCATEGORIA = 'M'
  AND A.NIVELHIERARQUIA = 1
```

---

## Passo a Passo — Configurar em Var - F7

1. Abra a Consulta Criação e carregue o SQL `consulta_cadastro_novo.sql`.
2. Pressione **F7** para abrir o cadastro de variáveis.
3. Cadastre cada variável conforme a especificação acima:
   - `:LS1` → Tipo **Lista** (Retorno **Literal**), padrão `TODOS`. Cole a SQL da lista acima no quadro de consulta da variável.
   - `:NR1` → Tipo **Numérico**, padrão `30`
   - `:NR2` → Tipo **Numérico**, padrão `1`
4. Salve as variáveis e pressione **Run**.
5. Antes do Run, a tela exibirá o dropdown de Departamento e os dois filtros numéricos para ajuste.

---

## Colunas Retornadas
| Coluna | Descrição |
|---|---|
| DEPARTAMENTO | Categoria nível 1 |
| CODIGO_PRODUTO | SEQPRODUTO |
| DESCRICAO_PRODUTO | Descrição completa |
| EMPRESA | Número da empresa/loja |
| STATUS | ATIVO / INATIVO |
| ESTOQUE | Estoque disponível calculado |
| PEDIDOS_PENDENTES | Qtd em pedidos de compra abertos |
| ESTOQUE_MINIMO | ESTQMINIMOLOJA parametrizado |
| DATA_CADASTRO_PRODUTO | Data de inclusão do produto |
