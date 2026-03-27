---
description: Inicia a orquestração multi-agentes da Squad Varejo Insight (Lê Entradas, Aplica Papéis, Gera Saídas)
---
# Workflow de Análise Varejo Insight (Pipeline)

Sempre que o usuário utilizar **`/run-varejo`**, execute sequencialmente as seguintes operações operando como orquestrador da arquitetura (Simulando o processamento logístico real dos CSVs e Agentes).

1. **Leitura da Base (Intake):** Leia todos os arquivos disponíveis na pasta `squads/varejo-insight/bd_entrada/`.
2. **Processamento Inicial (Danilo):** Calcule a necessidade real de estoque vs capacidade da Loja, baseando-se no DNA do `agents/danilo-dados.agent.md`. Extraia giro diário etc.
3. **Refinamento Estético e Fisico (Gabi e Leonardo):** Revise as quantidades propostas para garantir Facing na Gôndola e que compras não dupliquem sobra de retaguarda (buscando as regras em seus respectivos `.agent.md`).
4. **Modulação Exógena (Clara):** Considere preço de promoção nas colunas do CSV para justificar aumento brusco de demanda por Elasticidade e Clima (`clara-clima.agent.md`).
5. **Finalização C-Level (Roberta Dashboard):** Condense o Output inteiro em `07-dashboard-aprovado.md` salvo na `bd_saida` focado nos pilares Financeiros C-Level e Action Items (`roberta-relatorios.agent.md`).
6. **Integração ERP:** Quebre as informações aprovadas nos arquivos mecânicos e crie eles OBRIGATORIAMENTE em `bd_saida/ajuste_rop_erp.csv` e `bd_saida/pedidos_compra_erp.csv` utilizando separador ponto e vírgula (;). 
7. **Notificação final:** Avise o usuário que o Painel no Navegador pode ser atualizado e os CSVs já estão prontos.
