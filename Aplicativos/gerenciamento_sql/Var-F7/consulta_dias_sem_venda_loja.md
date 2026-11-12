# Consulta de Dias Sem Venda por Loja (Estoque Sem Giro)

Consulta otimizada com CTEs materializadas (`/*+ MATERIALIZE */`) para auditar produtos com estoque disponível diferente de zero e apurar os dias sem venda por loja no ERP Totvs Consinco.

---

### Arquivo SQL Oficial
- Caminho: `c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\gerenciamento_sql\querys\consulta_dias_sem_venda_loja.sql`

---

### Configuração de Variáveis de Tela (`Var - F7`)

| Variável | Tipo | Título / Descrição | Valor Padrão / Exemplo | Comportamento |
| :--- | :--- | :--- | :--- | :--- |
| **`NR1`** | Numérico | Dias de Carência Cadastro Novo | `60` | Define a janela (em dias) para tratar produtos recém-cadastrados sem venda (se vazio, assume `60`). |
| **`LT1`** | Texto | Código das Empresas / Lojas | `1,2,3,4,5,6,7,8,11,12,13,14,15,17,18` | Lista de lojas separadas por vírgula. |
| **`LT2`** | Texto | Filtro de Dias Sem Venda | `>=30` *(ou Vazio)* | Permite operadores como `>30`, `>=60`, `<15`, `<=10`, `=45` ou valor exato. |
| **`LT4`** | Texto | Status de Compra (A / I) | `A` | Digite `A` para Ativos, `I` para auditar Inativos com estoque residual, ou `A,I` (ou vazio) para ambos. |

---

### Expurgos Automáticos Embutidos
- Apenas mercadorias para revenda (`FINALIDADEFAMILIA = 'R'`).
- Expurgo de departamentos: `ALMOX`, `SERVI`, `ALIMENTO` e `INATIV`.
- Expurgo de categorias de Nível 2 e subcategorias filhas (via `CTE_FAM_EXPURGO`): **Frutas e Verduras**, **Padaria Baklizi** e **Padaria Industrial**.
- Expurgo fixo inicial de códigos de produto (`SEQPRODUTO NOT IN (15762, 15764, 15765)`).

