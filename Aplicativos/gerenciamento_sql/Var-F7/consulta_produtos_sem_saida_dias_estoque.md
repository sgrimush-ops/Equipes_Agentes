# Consulta de Produtos Sem Saída / Dias Sem Movimentação de Estoque

Consulta analítica para apurar produtos ativos sem movimentação de saída ou sem entrada recente por unidade/empresa no ERP Totvs Consinco.

---

### Arquivo SQL Oficial
- Caminho: `c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\gerenciamento_sql\querys\consulta_produtos_sem_saida_dias_estoque.sql`

---

### Configuração de Variáveis de Tela (`Var - F7`)

| Variável | Tipo | Título / Descrição | Valor Padrão / Exemplo | Comportamento |
| :--- | :--- | :--- | :--- | :--- |
| **`NR1`** | Numérico | Código do Produto | `0` | `0` traz todos os produtos; informe o código (ex: `38561`) para filtrar um produto específico. |
| **`NR2`** | Numérico | Dias Mínimos Sem Saída | `0` | `0` desativa o filtro; informe (ex: `30`) para trazer apenas produtos sem saída há 30 dias ou mais. |
| **`NR3`** | Numérico | Dias Mínimos Sem Entrada | `0` | `0` desativa o filtro; informe (ex: `60`) para trazer produtos cuja última entrada/compra ocorreu há 60 dias ou mais. |
| **`NR4`** | Numérico | Dias Mínimos de Cadastro | `0` | `0` traz tudo; informe (ex: `90`) para filtrar apenas itens cadastrados há mais de 90 dias. |
| **`LT1`** | Texto | Código das Empresas / Lojas | `1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18` | Lista de lojas/CDs separadas por vírgula. |
| **`LT2`** | Texto | Filtro de Estoque Atual | *(Vazio)* | Permite operadores como `>0`, `>=10`, `<5`, `=0` ou valor exato. |
| **`LT3`** | Texto | Formas de Abastecimento | `M,C,I,L` | Letras das formas de abastecimento permitidas (`M`, `C`, `I`, `L`, etc.). |

---

### Colunas Retornadas

1. **`DEPARTAMENTO`**: Categoria mercadológica de nível 1.
2. **`APELIDO_COMPRADOR`**: Apelido do comprador gestor da família (`MAX_COMPRADOR.APELIDO`).
3. **`SEQPRODUTO`**: Código do produto (`MAP_PRODUTO.SEQPRODUTO`).
4. **`DESCCOMPLETA`**: Descrição do produto.
5. **`FORMA_ABASTECIMENTO`**: Letra da forma de abastecimento (`MAP_FAMDIVISAO.FORMAABASTECIMENTO`).
6. **`EMPRESA_CD`**: Código da loja / CD (`MRL_PRODUTOEMPRESA.NROEMPRESA`).
7. **`ESTOQUE_ATUAL`**: Saldo disponível (`Loja + Depósito - Reservas`).
8. **`DATA_ULT_SAIDA`**: Data real do último movimento de saída (`B.DTAULTMOVSAIDA`). Fica em branco se nunca saiu.
9. **`DIAS_SEM_SAIDA`**: Quantidade de dias corridos desde a última saída (ou desde o cadastro se nunca saiu).
10. **`DATA_ULT_ENTRADA`**: Data da última entrada física / compra no estoque (`B.DTAULTMOVENTRADA` ou `B.DTAULTCOMPRA`).
11. **`DIAS_SEM_ENTRADA`**: Quantidade de dias corridos desde a última entrada no estoque.
12. **`DATA_CADASTRO`**: Data de inclusão do produto (`A.DTAHORINCLUSAO`).

---

### Expurgos Automáticos Embutidos
- Expurgo dos departamentos `ALMOXARIFADO`, `SERVIÇOS` e `NÃO ALIMENTOS`.
- Expurgo das subcategorias de Nível 2 em Perecíveis: **Frutas E Verduras**, **Padaria Baklizi** e **Padaria Industrial** (incluindo validação de hierarquia pai/filho).
