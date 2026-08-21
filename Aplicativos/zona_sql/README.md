# ⚡ ZONA SQL - Simulador & Mentor Consinco (Oracle ERP)

Um ambiente interativo e autônomo para **treinamento prático, desenvolvimento de consultas e aprendizado das regras do ERP Totvs Consinco / Oracle**.

---

## 🎯 Por que a Zona SQL foi criada?
Sites comuns de SQL (como W3Schools ou SQLiteOnline) utilizam esquemas genéricos (`Customers`, `Orders`, `Products`) que **não refletem o mundo real do ERP Consinco**, nem preparam você para os desafios críticos do dia a dia (como *hints* `/*+ MATERIALIZE */`, cálculo correto de estoque disponível sem duplicar saldos, bypass do validador *"Não é uma consulta"*, tratamento de embalagens com `QTDEMBALAGEM = 1`, e parametrização com `Var - F7`).

A **Zona SQL** reúne em uma interface visual completa:
1. **Banco de Dados Realista de Varejo:** Pré-carregado com as tabelas centrais do Consinco (`MAP_PRODUTO`, `MRL_PRODUTOEMPRESA`, `MAP_CATEGORIA`, `MRL_CUSTODIA`, `FI_TITULO`, `MSU_PEDIDOSUPRIM`, `MAX_EMPRESA`, `MAX_COMPRADOR`, etc.) e dados reais de lojas (1 a 18), compradores e estoques.
2. **Catálogo Oficial de 4.515 Tabelas:** Dicionário completo de tabelas e colunas integrado para busca instantânea.
3. **Motor com Emulação Oracle:** Suporta funções como `NVL()`, `TO_CHAR()`, `TO_DATE()`, `TO_NUMBER()`, `TRUNC()`, `SYSDATE()`, `INSTR()`, `SUBSTR()`, `DECODE()`, `REGEXP_LIKE()` e blocos de CTEs.
4. **Guardião de Regras Consinco (Linter em Tempo Real):** Alerta imediatamente se você digitar código com risco de erro fatal no Totvs SGI (como comentários `--`, alias com aspas duplas causando `ORA-00923`, coluna `STATUSVENDA` inexistente em `MRL_PRODUTOEMPRESA`, ou joins cartesianos).
5. **Mentor Didático de IA:** Decompõe a query em português claro, explicando o que cada tabela e join está fazendo.
6. **Trilha de Missões Práticas:** Desafios progressivos com verificação automática do resultado.
7. **Simulador de Variáveis de Tela (`Var - F7`):** Teste suas consultas dinâmicas com `:NROEMPRESA`, `:NR1`, `:LS1`, `:DT1` e `:LT1`.

---

## 🚀 Como Iniciar

### Opção 1: Pelo arquivo `.bat` (1 Clique no Windows)
Dê um duplo clique no arquivo:
```
c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\zona_sql\iniciar_zona_sql.bat
```
Ele abrirá seu navegador padrão automaticamente em `http://127.0.0.1:8550`.

### Opção 2: Pelo Terminal
```bash
cd c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\zona_sql
python server.py
```
Acesse: `http://127.0.0.1:8550`

---

## 🧩 Principais Recursos da Interface

| Recurso | Descrição |
| :--- | :--- |
| **📁 Explorador de Tabelas** | Lista todas as tabelas ativas com contagem de registros. Clique em `👁️` para ver colunas e 20 linhas de amostra, ou `📝` para gerar um `SELECT *` no editor. |
| **📚 Busca no Dicionário** | Pesquise instantaneamente por qualquer uma das 4.515 tabelas ou colunas do schema oficial Consinco. |
| **💡 Modelos / Snippets** | Modelos homologados prontos: *Bypass Consinco*, *Preço Vigente com NVL*, *Join de Embalagem Qtd=1*, *Vendas Oficiais MRL_CUSTODIA*, etc. |
| **⚡ Gaveta Var - F7** | Alterne lojas (1 a 18), fornecedores (:NR1) e períodos (:DT1 / :DT2) para testar queries parametrizadas. |
| **🛡️ Guardião Consinco** | Validação sintática e de boas práticas enquanto você digita no editor. |
| **🎓 Mentor Didático** | Clique em *"✨ Explicar Query"* para entender a modelagem, grão e cálculos da consulta. |
| **📊 Grade de Dados** | Visualização tabular dos dados retornados, ordenação, tempo de execução (ms) e exportação para CSV ou Excel. |
| **🧹 Limpar p/ Consinco** | Remove todos os comentários do código para colar diretamente no painel Consulta Criação do SGI sem erros de quebra de linha. |

---

## 🏆 Trilha de Aprendizado Inclusa

1. **Missão 1 (Básico):** Conhecendo os Produtos Ativos da Loja 1 (`MAP_PRODUTO` + `MRL_PRODUTOEMPRESA`).
2. **Missão 2 (Joins):** Hierarquia Comercial e Departamentos Nível 1 (`MAP_CATEGORIA`).
3. **Missão 3 (Cálculos):** Cálculo do Estoque Disponível Real abatendo reservas de venda e recebimento.
4. **Missão 4 (Oracle):** Preço Vigente Promocional vs Normal com `NVL` e `NULLIF`.
5. **Missão 5 (Performance):** CTE Materializada com Hint `/*+ MATERIALIZE */` e Bypass do validador (`SELECT * FROM (...)`).
6. **Missão 6 (Parametrização):** Parametrização dinâmica com variáveis bind `Var - F7` (`:NROEMPRESA`, `:NR1`).

---

## 🛠️ Como Recarregar ou Re-gerar o Banco de Dados

Para re-popular o banco do simulador com dados atualizados do workspace:
```bash
cd c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\zona_sql
python database\seed_data.py
```
