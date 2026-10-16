# Tarefa: [Título da Demanda SQL]

- **ID**: {TIMESTAMP}_{SLUG}
- **Origem**: Hermes Agent
- **Data de Criação**: {DATA_HORA}
- **Tipo**: SQL / Consulta Consinco
- **Prioridade**: Alta | Média | Baixa
- **Status**: Pendente

---

## 🎯 Objetivo de Negócio
Descreva de forma clara o que o usuário ou a rotina precisa analisar.
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
*Aguardando processamento...*
