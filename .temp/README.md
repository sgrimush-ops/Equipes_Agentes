# 🎮 GPU Hunter Pro | Monitor de Parcelamento Sem Juros (RTX 5070 Ti 16GB)

Ferramenta desenvolvida para cotar, registrar e analisar o **Parcelamento Sem Juros (10x vs 12x)**, o **Preço Total do Produto a Prazo**, a **Menor Parcela Mensal** e o **Custo por FPS em 1440p e 4K Nativo** dedicada à nova geração **NVIDIA GeForce RTX 5070 Ti (16GB GDDR7)** nas três principais varejistas de hardware do Brasil:
1. **Pichau** (`pichau.com.br`) - **12x Sem Juros**
2. **TerabyteShop** (`terabyteshop.com.br`) - **12x Sem Juros**
3. **KaBuM!** (`kabum.com.br`) - **10x Sem Juros**

---

## 💳 Foco Exclusivo em Parcelamento Sem Juros
A ferramenta analisa estritamente:
- **Menor Parcela Mensal Sem Juros (10x ou 12x)** (alívio no fluxo de caixa mensal);
- **Preço Total do Produto a Prazo Sem Juros**;
- **Comparativo Direto de Lojas (12x na Pichau/Terabyte vs 10x na KaBuM!)**.

---

## 🏆 Resumo Financeiro & Comparativo por Loja: RTX 5070 Ti (16GB GDDR7)

| Loja | Condição de Parcelamento | Menor Parcela Mensal | Preço Total Sem Juros | Impacto no Orçamento Familiar |
| :--- | :--- | :--- | :--- | :--- |
| 🔴 **Pichau** | **12x Sem Juros** | **R$ 774,51 / mês** | **R$ 9.294,11** | 🥇 **Menor Parcela Mensal** (Economia de R$ 154,90/mês vs KaBuM) |
| 🟢 **TerabyteShop** | **12x Sem Juros** | **R$ 813,63 / mês** | **R$ 9.763,53** | 🥈 **2ª Melhor Parcela** (Gainward Phoenix Triplo Fan) |
| 🟠 **KaBuM!** | **10x Sem Juros** | **R$ 929,41 / mês** | **R$ 9.294,11** | 🥉 **Mesmo Total Final**, porém parcela mensal +R$ 154,90 mais pesada |

---

## ⚙️ Especificações & Desempenho: NVIDIA GeForce RTX 5070 Ti

| Métrica | Especificação & Valor | Detalhes Técnicos |
| :--- | :--- | :--- |
| **Menor Parcela Sem Juros** | **12x de R$ 774,51** | Zotac Solid SFF Triplo Fan na Pichau |
| **Preço Total Sem Juros** | **R$ 9.294,11** | Preço final sem acréscimo de juros |
| **Desempenho 1440p Ultra** | **145 FPS Médio** | R$ 64,10 / FPS Total a Prazo |
| **Desempenho 4K Nativo** | **92 FPS Médio Nativo** | R$ 101,02 / FPS Total (R$ 8,42/mês por FPS gerado) |
| **Memória VRAM & Largura de Banda** | **16 GB GDDR7 (256-bit)** | 896 GB/s de largura de banda |
| **Consumo Térmico (TDP)** | **300W** | Refrigeração Triplo Fan com backplate reforçado |
| **Prontidão DLSS 5 (Novembro/2026)** | **Filtro Neural de Texturas** | 16GB VRAM garantem fotorrealismo por IA em 4K nativo |

---

## 📈 Funcionalidades da Aplicação

- **Varredura Exclusiva de RTX 5070 Ti Sem Juros:** Rastreamento do valor a prazo e quantidade de parcelas sem juros.
- **Comparativo Financeiro de Lojas (10x vs 12x):** Demonstração do impacto no fluxo de caixa mensal.
- **Top 3 Melhores Opções Sem Juros por Loja:** Identificação automática dos 3 melhores negócios em cada site parceiro.
- **Simulador de Capacidade Mensal:** Slider interativo para o usuário ajustar quanto pode pagar por mês no cartão (R$ 500 a R$ 1.500/mês).
- **Gravação Automática Diária em SQLite:** Todas as cotações são salvas com data no banco (`price_history.db`).
- **Monitor de Oscilação 24h e 7 Dias:** Alerta de Menor Preço Histórico (*All-Time Low*).
- **Gráficos Interativos (Chart.js):** Preço total vs parcela mensal e custo total por frame.
- **Exportação CSV:** Download imediato da base de dados sem juros para Excel.

---

## 🚀 Como Executar

### 1. Interface Web Interativa (Recomendado)
- Dê dois cliques em **[`iniciar.bat`](file:///c:/Users/usr/Downloads/Equipes_Agentes/.temp/iniciar.bat)** ou execute:
  ```bash
  python server.py
  ```
- O navegador abrirá automaticamente em: **`http://127.0.0.1:5000`**

### 2. Interface via Linha de Comando (CLI)
```bash
python cli_comparador.py
```
