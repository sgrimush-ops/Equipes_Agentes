# Tarefa: Validar Conexao e Teste Piloto Hermes

- **ID**: 20261016_105613_validar_conexao_e_teste_piloto_herm
- **Origem**: Hermes Agent
- **Data de Criação**: 16/10/2026 10:56:13
- **Tipo**: SQL / Consulta Consinco
- **Prioridade**: Alta | Média | Baixa
- **Status**: Pendente

---

## 🎯 Objetivo de Negócio
Criar uma consulta simples de teste e validar a comunicacao entre o Hermes Agent e o Antigravity no workspace Equipes_Agentes.
*Exemplo: Relatório de produtos sem venda nos últimos 30 dias com estoque ativo.*

## 📋 Especificações e Parâmetros
- **Tabelas / Módulos de Interesse**: (ex: `MRL_PRODUTOEMPRESA`, `MRL_CUSTODIA`, `MAP_PRODUTO`)
- **Tela de Destino**: Consulta Criação / Var-F7 / Relatório Externo
- **Filtros Obrigatórios**:
  - Filiais: `:LS1` ou `:LT1`
  - Período: `:DT1` a `:DT2`
  - Fornecedor ou Categoria: `:LS2`
- **Regras Específicas**: (ex: Não usar comentários no SQL, utilizar `/*+ MATERIALIZE */` em CTEs, limitar listas Var-F7 a 145 caracteres)

## 📦 Entrega Esperada
1. Arquivo `.sql` pronto para importação.
2. Arquivo `.md` explicativo da parametrização das variáveis da tela `Var - F7`.

---

## 🏁 Relatório de Execução (Preenchido pelo Antigravity ao concluir)
---

## 🏁 Relatório de Execução (Concluído pelo Antigravity)
- **Data de Finalização**: 16/10/2026 10:57:45
- **Status**: Concluído com Sucesso

### 📝 Resumo da Entrega:
Consulta de teste gerada seguindo as regras do ERP Totvs Consinco (sem comentarios, clausula MATERIALIZE na CTE, filtro por LT1 e NR1, e lista restrita de lojas da rede). Documentacao Var-F7 gerada com sucesso.

### 📁 Arquivos Gerados / Modificados:
- `Aplicativos/gerenciamento_sql/querys/teste_piloto_hermes.sql`
- `Aplicativos/gerenciamento_sql/Var-F7/teste_piloto_hermes.md`
