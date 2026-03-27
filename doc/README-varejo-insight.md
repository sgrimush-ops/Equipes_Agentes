# Squad Varejo Insight (Líder: Danilo Dados)

Esta squad é especializada em inteligência de abastecimento e gestão de estoque para redes de varejo. Ela orquestra múltiplos agentes para garantir que as lojas tenham o produto certo, na quantidade certa, minimizando rupturas e excessos de estoque.

## 👥 Agentes e Responsabilidades

- **🤵 Danilo Dados (Analista de Dados):** O cérebro analítico. Processa giros de estoque, calcula o Ponto de Pedido (ROP) com lead time dinâmico de 2-4 dias e sugere reposições baseadas no saldo do CD.
- **👸 Gabi Gôndola (Visual Merchandising):** Garante a estética e o "efeito de massa". Suas travas de estoque de apresentação (facing) anulam sugestões baixas de reposição para itens em exposição.
- **📦 Leonardo Logística (Logística de Loja):** Otimiza o espaço físico. Identifica sobras no depósito da loja para evitar pedidos desnecessários ao CD.
- **🌤️ Clara Clima (Inteligência Sazonal):** Ajusta o OTB (Open-to-Buy) com base em previsões climáticas e histórico promocional.
- **🛒 Paulo Pedidos (Gestor do CD):** Responsável pelo "Estoque Pulmão" no **Centro de Distribuição (Filial 15)**. Garante cobertura de 15 dias para a rede, comprando de fornecedores externos em fardos/caixas.
- **📊 Roberta Relatórios (Relator Executivo):** Consolida os dados em KPIs estratégicos e alertas de ação para a diretoria.

## ⚙️ Regras de Negócio Implementadas

1. **CD Centralizado:** A Filial 15 é o hub oficial de distribuição.
2. **Lead Time Dinâmico:** Ciclo de reposição entre 2 e 4 dias.
3. **Padrão de Segurança CD:** Manutenção de 15 dias de giro global no CD.
4. **Conversão de Embalagem:** Todas as ordens de compra para o CD são convertidas automaticamente para a unidade de venda do fornecedor (caixas/fardos).

## 🚀 Como Executar

Para iniciar a orquestração desta squad, use o comando:

```
/run-varejo
```

Ou através do menu principal:
1. Digite `/Equipes_agentes`
2. Selecione **Executar squad**
3. Escolha **varejo-insight**
