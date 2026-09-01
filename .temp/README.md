# 🎮 GPU Hunter Pro | Monitor de Preços, Histórico Diário & Custo x Benefício

Ferramenta desenvolvida para cotar, registrar e analisar o **Histórico Diário de Preços**, o **Custo por FPS em 1440p e 4K Nativo** e a **Simulação de Parcelamento em 15x** das duas placas mais equilibradas da nova geração **NVIDIA Blackwell (RTX 5070 e RTX 5070 Ti)** nas três principais varejistas de hardware do Brasil:
1. **KaBuM!** (`kabum.com.br`)
2. **Pichau** (`pichau.com.br`)
3. **TerabyteShop** (`terabyteshop.com.br`)

---

## 🏆 Resumo Comparativo: RTX 5070 vs RTX 5070 Ti (1440p vs 4K Nativo & 15x)

| Posição | Modelo | Menor Preço (PIX) | Plano 15x (+10% acréscimo) | FPS 1440p | R$/FPS 1440p | FPS 4K Nativo | R$/FPS 4K Nativo | Veredito |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **🥇 Campeã C/B Geral** | **NVIDIA RTX 5070 (12GB GDDR7)** | **R$ 4.899,99** | **15x de R$ 422,74** (Total R$ 6.341,16) | **115 FPS** | **R$ 42,61 / FPS** | 72 FPS | **R$ 68,06 / FPS** | **Menor Custo por Frame:** Excelente para Quad HD (1440p Ultra) e 4K com DLSS 4. Consome apenas 250W. |
| **🥈 Campeã 4K & Longevidade** | **NVIDIA RTX 5070 Ti (16GB GDDR7)** | **R$ 8.199,99** | **15x de R$ 707,45** (Total R$ 10.611,76) | **145 FPS** | R$ 56,55 / FPS | **92 FPS** (+28%) | R$ 89,13 / FPS | **A Escolha para 4K Nativo:** Possui 16GB de VRAM em barramento de 256-bit (896 GB/s), entregando 92 FPS sólidos em 4K nativo. |

> **Nota sobre o Parcelamento:** Os preços anunciados no PIX contam com ~15% de desconto à vista. A simulação em 15 parcelas aplica acréscimo médio de 10% sobre o preço a prazo para absorver o parcelamento estendido no cartão/financiamento. A diferença na prestação é de **+R$ 284,71/mês** para pular da 5070 para a 5070 Ti.

---

## 🚀 Prontidão Tecnológica: NVIDIA DLSS 5 (Novembro / 2026)

- **Filtro Neural de Texturas por IA:** Em Novembro de 2026, o DLSS 5 introduz a reconstrução neural profunda de materiais e texturas em tempo real, gerando microdetalhes fotográficos físicos (porosidade de pele, rugosidade de asfalto, tecidos e reflexos metálicos hiper-realistas).
- **Impacto na RTX 5070 (12GB):** Total compatibilidade nativa com os Tensor Cores de 5ª geração Blackwell. Ideal para 1440p Ultra com DLSS 5 a 110+ FPS. Em 4K Extremo com Path Tracing, a VRAM operará próxima de 11.5 GB.
- **Impacto na RTX 5070 Ti (16GB):** A placa perfeita para DLSS 5 em 4K. Seus 16GB GDDR7 e 896 GB/s de banda de memória fornecem folga de mais de 3.2 GB de VRAM com todos os filtros neurais ativos a 90+ FPS constantes.

---

## 📈 Funcionalidades da Aplicação

- **Análise Dedicada de 4K Nativo:** Métricas de FPS médio ultra e custo por frame em 4K nativo (sem upscaler) lado a lado com 1440p.
- **Simulador de Parcelamento em 15x:** Painel financeiro interativo que calcula a prestação mensal (+10% de acréscimo) e compara o esforço financeiro entre os modelos.
- **Prontidão DLSS 5:** Avaliação de ocupação de VRAM e largura de banda para a nova tecnologia de fotorrealismo por IA.
- **Gravação Automática por Dia:** A cada varredura diária, todas as cotações são arquivadas com data no banco SQLite (`price_history.db`).
- **Monitor de Oscilação 24h e 7 Dias:** Mede em percentual (%) e valor nominal a queda ou subida de cada placa com alerta de *All-Time Low*.
- **Gráficos Interativos (Chart.js):** Curvas diárias temporais, barras duplas de R$/FPS (1440p vs 4K) e comparação de Preço à Vista vs Prestação Mensal 15x.
- **Exportação do Histórico Completo em CSV:** Baixe o arquivo `.csv` para auditar no Excel.

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


