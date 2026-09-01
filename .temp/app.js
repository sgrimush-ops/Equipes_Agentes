/**
 * GPU Hunter Pro - Frontend Application Logic
 * Foco exclusivo em RTX 5070 e RTX 5070 Ti (Alto Custo-Benefício)
 */

let globalData = null;
let chartCostFps = null;
let chartPerfPrice = null;
let chartDailyHistory = null;
let currentHistoryDays = 30;

document.addEventListener('DOMContentLoaded', () => {
  fetchGPUData();
  loadHistoryChart();
  setInterval(checkUpdateStatus, 3000);
});

async function fetchGPUData() {
  try {
    const response = await fetch('/api/gpus');
    const result = await response.json();
    
    if (result.status === 'success' && result.data) {
      globalData = result.data;
      renderAll(globalData);
    }
  } catch (error) {
    console.error('Erro ao buscar dados da API:', error);
  }
}

async function checkUpdateStatus() {
  try {
    const response = await fetch('/api/status');
    const res = await response.json();
    const statusText = document.getElementById('status-text');
    const btnRefresh = document.getElementById('btn-refresh');
    
    if (res.is_updating) {
      statusText.innerHTML = '<span style="color:#38bdf8;">Varrendo lojas ao vivo (5070 & 5070 Ti)...</span>';
      if (btnRefresh) btnRefresh.disabled = true;
    } else {
      statusText.textContent = 'Monitorando 3 Lojas (RTX 5070 & 5070 Ti)';
      if (btnRefresh) btnRefresh.disabled = false;
    }
  } catch (e) {}
}

async function triggerRefresh() {
  const btnRefresh = document.getElementById('btn-refresh');
  if (btnRefresh) {
    btnRefresh.disabled = true;
    btnRefresh.innerHTML = '<span>Varrendo & Gravando...</span>';
  }
  
  try {
    await fetch('/api/refresh', { method: 'POST' });
    alert('Varredura ao vivo iniciada para RTX 5070 e RTX 5070 Ti nas 3 lojas. O snapshot do dia será atualizado!');
    setTimeout(() => { fetchGPUData(); loadHistoryChart(); }, 4000);
    setTimeout(() => { fetchGPUData(); loadHistoryChart(); }, 8000);
  } catch (e) {
    console.error('Erro ao acionar refresh:', e);
  }
}

function renderAll(data) {
  renderTickerCards(data.variation_stats);
  renderChampion(data);
  renderModelsGrid(data.model_stats);
  renderSimulator15x(data.model_stats, data.recommendation);
  renderCharts(data.model_stats);
  renderOffersTable();
  renderDLSS5Section(data.recommendation);
  renderVerdict(data.recommendation);
  updateBudgetSimulation();
}


// 1. Ticker de Oscilação Diária (24h / 7d / Recorde)
function renderTickerCards(variations) {
  const container = document.getElementById('ticker-cards-grid');
  if (!container || !variations) return;

  container.innerHTML = '';
  const models = ['RTX 5070', 'RTX 5070 Ti'];

  models.forEach(model => {
    const v = variations[model];
    if (!v) return;

    const card = document.createElement('div');
    card.className = `ticker-card ${v.is_at_all_time_low ? 'all-time-low-border' : ''}`;

    let badge24Class = 'badge-stable';
    let icon24 = '▬';
    if (v.pct_24h < 0) {
      badge24Class = 'badge-fall';
      icon24 = '▼';
    } else if (v.pct_24h > 0) {
      badge24Class = 'badge-rise';
      icon24 = '▲';
    }

    let badge7Class = 'badge-stable';
    let icon7 = '▬';
    if (v.pct_7d < 0) {
      badge7Class = 'badge-fall';
      icon7 = '▼';
    } else if (v.pct_7d > 0) {
      badge7Class = 'badge-rise';
      icon7 = '▲';
    }

    card.innerHTML = `
      <div class="ticker-card-top">
        <h3 class="ticker-model-name">${model}</h3>
        ${v.is_at_all_time_low ? '<span class="all-time-low-tag">🏷️ MENOR PREÇO HISTÓRICO</span>' : ''}
      </div>

      <div class="ticker-price-main">${formatCurrency(v.current_min_price)} <span style="font-size:0.85rem; color:var(--text-muted); font-weight:400;">(à vista)</span></div>

      <div class="ticker-variations-row">
        <span class="var-badge ${badge24Class}" title="Variação em relação a ontem">
          24h: ${icon24} ${Math.abs(v.pct_24h)}% (${v.diff_24h >= 0 ? '+' : ''}${formatCurrency(v.diff_24h)})
        </span>
        <span class="var-badge ${badge7Class}" title="Variação nos últimos 7 dias">
          7d: ${icon7} ${Math.abs(v.pct_7d)}%
        </span>
      </div>

      <div class="ticker-record-bar">
        <span>Menor já visto: <strong>${formatCurrency(v.all_time_low)}</strong></span>
        <span>Máx: ${formatCurrency(v.all_time_high)}</span>
      </div>
    `;

    container.appendChild(card);
  });
}

// 2. Gráfico do Histórico Diário de Preços (30 Dias)
async function loadHistoryChart() {
  const storeFilter = document.getElementById('history-store-filter')?.value || 'all';
  try {
    const res = await fetch(`/api/history?days=${currentHistoryDays}&store=${storeFilter}`);
    const data = await res.json();
    if (data.status === 'success' && data.timeline) {
      renderHistoryChart(data.timeline);
    }
  } catch (e) {
    console.error('Erro ao carregar histórico:', e);
  }
}

function changeHistoryPeriod(days) {
  currentHistoryDays = days;
  document.querySelectorAll('.btn-time-filter').forEach(btn => {
    btn.classList.toggle('active', parseInt(btn.getAttribute('data-days')) === days);
  });
  loadHistoryChart();
}

function renderHistoryChart(timeline) {
  const ctx = document.getElementById('chart-daily-history');
  if (!ctx || !timeline) return;

  if (chartDailyHistory) chartDailyHistory.destroy();

  const formattedDates = timeline.dates.map(d => {
    const parts = d.split('-');
    return `${parts[2]}/${parts[1]}`;
  });

  const series5070 = timeline.series['RTX 5070']?.min_prices || [];
  const series5070ti = timeline.series['RTX 5070 Ti']?.min_prices || [];

  chartDailyHistory = new Chart(ctx, {
    type: 'line',
    data: {
      labels: formattedDates,
      datasets: [
        {
          label: 'RTX 5070 (Menor Preço)',
          data: series5070,
          borderColor: '#76B900',
          backgroundColor: 'rgba(118, 185, 0, 0.09)',
          borderWidth: 2.8,
          pointRadius: 4.5,
          pointHoverRadius: 7,
          pointBackgroundColor: '#76B900',
          tension: 0.25,
          fill: true
        },
        {
          label: 'RTX 5070 Ti (Menor Preço)',
          data: series5070ti,
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.06)',
          borderWidth: 2.8,
          pointRadius: 4.5,
          pointHoverRadius: 7,
          pointBackgroundColor: '#38bdf8',
          tension: 0.25,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          labels: { color: '#c9d1d9', font: { family: 'Inter', size: 12 } }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#8b949e', font: { size: 11 } },
          grid: { color: 'rgba(255, 255, 255, 0.04)' }
        },
        y: {
          ticks: {
            color: '#8b949e',
            callback: (v) => `R$ ${v/1000}k`
          },
          grid: { color: 'rgba(255, 255, 255, 0.06)' }
        }
      }
    }
  });
}

// 3. Hero do Campeão
function renderChampion(data) {
  const winner = data.winner;
  const rec = data.recommendation;
  if (!winner) return;

  document.getElementById('winner-title').textContent = `${winner.gpu_model} (${winner.brand})`;
  document.getElementById('winner-desc').textContent = rec.verdict_summary || '';
  document.getElementById('winner-price').textContent = formatCurrency(winner.price_cash);
  document.getElementById('winner-store').textContent = `no PIX (${winner.store})`;
  
  const winner15x = document.getElementById('winner-15x');
  if (winner15x) {
    winner15x.textContent = `15x de ${formatCurrency(winner.installment_15x_val)}`;
  }
  
  document.getElementById('winner-cost-fps').textContent = `R$ ${winner.cost_per_fps_1440p} / FPS`;
  
  const winner4k = document.getElementById('winner-cost-fps-4k');
  if (winner4k) {
    winner4k.textContent = `R$ ${winner.cost_per_fps_4k} / FPS`;
  }
  
  const winnerLink = document.getElementById('winner-link');
  if (winnerLink) {
    winnerLink.href = winner.url;
  }
}

// 4. Grid dos 2 Modelos (5070 vs 5070 Ti)
function renderModelsGrid(modelStats) {
  const container = document.getElementById('models-grid');
  if (!container || !modelStats) return;

  container.innerHTML = '';
  const models = ['RTX 5070', 'RTX 5070 Ti'];

  models.forEach(modelName => {
    const st = modelStats[modelName];
    if (!st) return;

    const isChampion = modelName === 'RTX 5070';
    const card = document.createElement('div');
    card.className = `model-card ${isChampion ? 'highlight' : ''}`;

    card.innerHTML = `
      <div>
        <div class="model-card-header">
          <div>
            <h3 class="model-card-name">${modelName}</h3>
            <span style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">${st.vram}</span>
          </div>
          <span class="model-tier-tag">${isChampion ? '🏆 MELHOR C/B GERAL' : '⚡ 16GB RECOMENDADA 4K'}</span>
        </div>

        <div class="specs-list">
          <div class="spec-row">
            <span class="spec-row-label">Consumo (TDP):</span>
            <span class="spec-row-val">${st.tdp}</span>
          </div>
          <div class="spec-row">
            <span class="spec-row-label">Desempenho Relativo:</span>
            <span class="spec-row-val">${st.perf_index} pts</span>
          </div>
          <div class="spec-row">
            <span class="spec-row-label">🎮 FPS 1440p Ultra:</span>
            <span class="spec-row-val font-bold">${st.avg_fps_1440p} FPS</span>
          </div>
          <div class="spec-row">
            <span class="spec-row-label">💸 R$/FPS (1440p):</span>
            <span class="spec-row-val text-green font-bold">R$ ${st.cost_per_fps_1440p} / FPS</span>
          </div>
          <div class="spec-row spec-highlight-4k">
            <span class="spec-row-label">🖥️ FPS 4K Nativo Ultra:</span>
            <span class="spec-row-val font-bold text-accent">${st.avg_fps_4k} FPS</span>
          </div>
          <div class="spec-row spec-highlight-4k">
            <span class="spec-row-label">💎 R$/FPS (4K Nativo):</span>
            <span class="spec-row-val text-accent font-bold">R$ ${st.cost_per_fps_4k} / FPS</span>
          </div>
        </div>
      </div>

      <div class="model-price-area">
        <div class="price-cash-block">
          <span class="model-price-label">Menor Preço à Vista (PIX c/ ~15% desc):</span>
          <div class="model-price-val">${formatCurrency(st.min_price)}</div>
        </div>

        <!-- Bloco 15x -->
        <div class="model-15x-box">
          <div class="model-15x-header">
            <span>💳 Plano em 15x (+10% acréscimo):</span>
            <span class="tag-15x">15x</span>
          </div>
          <div class="model-15x-val">${st.min_installment_15x_text} <span class="model-15x-sub">/ mês</span></div>
          <div class="model-15x-total">Total a prazo: <strong>${formatCurrency(st.min_price_15x_total)}</strong></div>
        </div>

        <div class="model-price-details">
          <span>Melhor na <strong>${st.best_store}</strong></span>
          <span>Méd: ${formatCurrency(st.avg_price)}</span>
        </div>

        <a href="${st.best_url}" target="_blank" class="btn btn-secondary" style="width:100%; margin-top:8px;">
          Ver Oferta na ${st.best_store} ↗
        </a>
      </div>
    `;
    container.appendChild(card);
  });
}

// 5. Seção de Simulação em 15x
function renderSimulator15x(modelStats, rec) {
  const container = document.getElementById('sim-15x-grid');
  if (!container || !modelStats) return;

  const st5070 = modelStats['RTX 5070'];
  const st5070ti = modelStats['RTX 5070 Ti'];
  if (!st5070 || !st5070ti) return;

  const diffMonth = st5070ti.min_installment_15x_val - st5070.min_installment_15x_val;
  const diffTotal = st5070ti.min_price_15x_total - st5070.min_price_15x_total;

  container.innerHTML = `
    <!-- Card 5070 -->
    <div class="sim-15x-card-item">
      <div class="sim-15x-card-top">
        <h3>RTX 5070 (12GB)</h3>
        <span class="badge-mini-green">MAIS ACESSÍVEL</span>
      </div>

      <div class="sim-15x-price-row">
        <span class="sim-15x-inst-big">15x de ${formatCurrency(st5070.min_installment_15x_val)}</span>
        <span class="sim-15x-cash-ref">ou ${formatCurrency(st5070.min_price)} no PIX à vista</span>
      </div>

      <ul class="sim-15x-details-list">
        <li><strong>Total a prazo (15x):</strong> ${formatCurrency(st5070.min_price_15x_total)}</li>
        <li><strong>R$ / FPS em 4K Nativo:</strong> R$ ${st5070.cost_per_fps_4k} (72 FPS)</li>
        <li><strong>R$ / FPS em 1440p:</strong> R$ ${st5070.cost_per_fps_1440p} (115 FPS)</li>
        <li><strong>Consumo:</strong> 250W (Fonte 650W recomendada)</li>
      </ul>
    </div>

    <!-- Comparador Central de Decisão -->
    <div class="sim-15x-bridge-card">
      <div class="bridge-title">⚖️ SALTO DE CATEGORIA</div>
      <div class="bridge-diff-val">+ ${formatCurrency(diffMonth)} <span style="font-size:0.9rem; font-weight:400; color:var(--text-sub);">/ mês em 15x</span></div>
      <div class="bridge-diff-total">Diferença total de ${formatCurrency(diffTotal)}</div>
      
      <div class="bridge-benefits-box">
        <div class="bridge-benefits-title">O que você ganha pagando +${formatCurrency(diffMonth)}/mês?</div>
        <div class="bridge-benefit-item">✨ <strong>+4GB GDDR7</strong> (16GB no total)</div>
        <div class="bridge-benefit-item">⚡ <strong>Barramento de 256-bit</strong> (896 GB/s de banda)</div>
        <div class="bridge-benefit-item">🚀 <strong>+20 FPS em 4K Nativo</strong> (92 FPS vs 72 FPS)</div>
        <div class="bridge-benefit-item">🛡️ <strong>Blindagem de 5+ anos</strong> contra falta de VRAM</div>
      </div>
    </div>

    <!-- Card 5070 Ti -->
    <div class="sim-15x-card-item highlight-ti">
      <div class="sim-15x-card-top">
        <h3>RTX 5070 Ti (16GB)</h3>
        <span class="badge-mini-blue">LONGEVIDADE 4K</span>
      </div>

      <div class="sim-15x-price-row">
        <span class="sim-15x-inst-big text-accent">15x de ${formatCurrency(st5070ti.min_installment_15x_val)}</span>
        <span class="sim-15x-cash-ref">ou ${formatCurrency(st5070ti.min_price)} no PIX à vista</span>
      </div>

      <ul class="sim-15x-details-list">
        <li><strong>Total a prazo (15x):</strong> ${formatCurrency(st5070ti.min_price_15x_total)}</li>
        <li><strong>R$ / FPS em 4K Nativo:</strong> R$ ${st5070ti.cost_per_fps_4k} (92 FPS)</li>
        <li><strong>R$ / FPS em 1440p:</strong> R$ ${st5070ti.cost_per_fps_1440p} (145 FPS)</li>
        <li><strong>Consumo:</strong> 300W (Fonte 750W recomendada)</li>
      </ul>
    </div>
  `;
}

// 6. Gráficos Chart.js
function renderCharts(modelStats) {
  if (!modelStats) return;

  const labels = ['RTX 5070', 'RTX 5070 Ti'];
  const costFps1440p = labels.map(l => modelStats[l]?.cost_per_fps_1440p || 0);
  const costFps4k = labels.map(l => modelStats[l]?.cost_per_fps_4k || 0);
  const cashPrices = labels.map(l => modelStats[l]?.min_price || 0);
  const inst15x = labels.map(l => modelStats[l]?.min_installment_15x_val || 0);

  const ctx1 = document.getElementById('chart-cost-fps');
  if (ctx1) {
    if (chartCostFps) chartCostFps.destroy();
    chartCostFps = new Chart(ctx1, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Custo por FPS 1440p (R$)',
            data: costFps1440p,
            backgroundColor: '#76B900',
            borderRadius: 6
          },
          {
            label: 'Custo por FPS 4K Nativo (R$)',
            data: costFps4k,
            backgroundColor: '#38bdf8',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#c9d1d9', font: { family: 'Inter', size: 12 } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: R$ ${ctx.raw.toFixed(2)} por frame gerado`
            }
          }
        },
        scales: {
          x: { ticks: { color: '#8b949e' }, grid: { display: false } },
          y: {
            ticks: {
              color: '#8b949e',
              callback: (v) => `R$ ${v}`
            },
            grid: { color: 'rgba(255,255,255,0.06)' }
          }
        }
      }
    });
  }

  const ctx2 = document.getElementById('chart-perf-price');
  if (ctx2) {
    if (chartPerfPrice) chartPerfPrice.destroy();
    chartPerfPrice = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            type: 'bar',
            label: 'Preço à Vista PIX (R$)',
            data: cashPrices,
            backgroundColor: 'rgba(168, 85, 247, 0.4)',
            borderColor: '#a855f7',
            borderWidth: 1.5,
            yAxisID: 'yCash',
            borderRadius: 6
          },
          {
            type: 'line',
            label: 'Prestação Mensal 15x (R$)',
            data: inst15x,
            borderColor: '#eab308',
            backgroundColor: '#eab308',
            yAxisID: 'yInst',
            pointRadius: 6,
            pointBackgroundColor: '#eab308',
            borderWidth: 2.5
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#c9d1d9', font: { family: 'Inter', size: 12 } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
            }
          }
        },
        scales: {
          x: { ticks: { color: '#8b949e' }, grid: { display: false } },
          yCash: {
            type: 'linear',
            position: 'left',
            ticks: {
              color: '#a855f7',
              callback: (v) => `R$ ${v/1000}k`
            },
            grid: { color: 'rgba(255,255,255,0.06)' }
          },
          yInst: {
            type: 'linear',
            position: 'right',
            ticks: {
              color: '#eab308',
              callback: (v) => `R$ ${v}`
            },
            grid: { display: false }
          }
        }
      }
    });
  }
}

// 7. Simulador de Orçamento
function updateBudgetSimulation() {
  const slider = document.getElementById('budget-slider');
  const display = document.getElementById('budget-value-display');
  const resultBox = document.getElementById('sim-result-box');
  if (!slider || !globalData || !globalData.model_stats) return;

  const budget = parseFloat(slider.value);
  display.textContent = formatCurrency(budget);

  const stats = globalData.model_stats;
  const p5070 = stats['RTX 5070']?.min_price || 4899.99;
  const p5070ti = stats['RTX 5070 Ti']?.min_price || 8199.99;
  const inst5070 = stats['RTX 5070']?.min_installment_15x_val || 422.74;
  const inst5070ti = stats['RTX 5070 Ti']?.min_installment_15x_val || 707.45;

  let recommendedModel = '';
  let tip = '';
  let leftover = 0;
  let neededForNext = 0;
  let instEquivalent = '';

  if (budget >= p5070ti) {
    recommendedModel = 'NVIDIA GeForce RTX 5070 Ti (16GB)';
    leftover = budget - p5070ti;
    instEquivalent = `Ou parcele em 15x de ${formatCurrency(inst5070ti)}/mês`;
    tip = `Excelente escolha! A 5070 Ti entrega 16GB de VRAM ideal para 4K Nativo e Path Tracing. Sobram ${formatCurrency(leftover)} no bolso para o restante do setup.`;
  } else if (budget >= p5070) {
    recommendedModel = 'NVIDIA GeForce RTX 5070 (12GB)';
    leftover = budget - p5070;
    neededForNext = p5070ti - budget;
    instEquivalent = `Ou parcele em 15x de ${formatCurrency(inst5070)}/mês`;
    tip = `Campeã de Custo x Benefício! Roda 4K Nativo a 72 FPS e 1440p Ultra com folga. Sobram ${formatCurrency(leftover)} no bolso (ou complete com ${formatCurrency(neededForNext)} para os 16GB da 5070 Ti).`;
  } else {
    recommendedModel = 'Orçamento Abaixo do Valor à Vista';
    neededForNext = p5070 - budget;
    instEquivalent = `Você pode parcelar a 5070 em 15x de ${formatCurrency(inst5070)}/mês!`;
    tip = `A placa mais em conta da nova geração (RTX 5070) custa ${formatCurrency(p5070)} à vista. Se preferir parcelar em 15x com +10% de acréscimo, a prestação fica em apenas ${formatCurrency(inst5070)}/mês.`;
  }

  resultBox.innerHTML = `
    <div class="sim-result-main">
      <h4>Recomendação Ideal para seu Orçamento:</h4>
      <div class="sim-gpu-name">${recommendedModel}</div>
      <div style="font-size:0.85rem; color:#eab308; font-weight:700; margin-bottom:4px;">💳 ${instEquivalent}</div>
      <p class="sim-gpu-tip">${tip}</p>
    </div>
    <div class="sim-budget-math">
      <span class="sim-math-label">${leftover >= 0 ? 'Saldo Restante à Vista:' : 'Falta para a 5070 à Vista:'}</span>
      <div class="sim-math-val ${leftover >= 0 ? 'text-green' : 'text-accent'}">
        ${formatCurrency(leftover >= 0 ? leftover : neededForNext)}
      </div>
    </div>
  `;
}

// 8. Tabela Geral de Ofertas
function renderOffersTable() {
  if (!globalData || !globalData.offers) return;

  const tbody = document.getElementById('offers-tbody');
  const countLabel = document.getElementById('offers-count-label');
  const filterModel = document.getElementById('filter-model').value;
  const filterStore = document.getElementById('filter-store').value;
  const filterPayment = document.getElementById('filter-payment').value;
  const filterSort = document.getElementById('filter-sort').value;

  let offers = [...globalData.offers];

  if (filterModel !== 'ALL') {
    offers = offers.filter(o => o.gpu_model === filterModel);
  }

  if (filterStore !== 'ALL') {
    offers = offers.filter(o => o.store_key === filterStore);
  }

  offers.sort((a, b) => {
    if (filterSort === 'score') return b.cost_benefit_score - a.cost_benefit_score;
    if (filterSort === 'price_asc') {
      if (filterPayment === 'cash') return a.price_cash - b.price_cash;
      if (filterPayment === 'card_15x') return (a.installment_15x_val || 0) - (b.installment_15x_val || 0);
      return a.price_card - b.price_card;
    }
    if (filterSort === 'installment_15x') {
      return (a.installment_15x_val || 0) - (b.installment_15x_val || 0);
    }
    if (filterSort === 'fps_cost_4k') {
      return (a.cost_per_fps_4k || 0) - (b.cost_per_fps_4k || 0);
    }
    if (filterSort === 'fps_cost_1440p') {
      return (a.cost_per_fps_1440p || 0) - (b.cost_per_fps_1440p || 0);
    }
    if (filterSort === 'price_desc') {
      if (filterPayment === 'cash') return b.price_cash - a.price_cash;
      if (filterPayment === 'card_15x') return (b.installment_15x_val || 0) - (a.installment_15x_val || 0);
      return b.price_card - a.price_card;
    }
    return 0;
  });

  countLabel.textContent = `Exibindo ${offers.length} ofertas consolidadas hoje (RTX 5070 & 5070 Ti)`;
  tbody.innerHTML = '';

  offers.forEach(o => {
    const tr = document.createElement('tr');
    
    let storeClass = 'store-kabum';
    if (o.store_key === 'pichau') storeClass = 'store-pichau';
    if (o.store_key === 'terabyte') storeClass = 'store-terabyte';

    const inst15xVal = o.installment_15x_val || Math.round((o.price_card * 1.10) / 15 * 100) / 100;
    const price15xTotal = o.price_15x_total || Math.round(o.price_card * 1.10 * 100) / 100;

    tr.innerHTML = `
      <td>
        <span class="store-tag ${storeClass}">${o.store_logo || o.store}</span>
      </td>
      <td>
        <strong style="color:#fff;">${o.gpu_model}</strong>
        <div class="gpu-subinfo">${o.vram || ''} • ${o.tdp || ''}</div>
      </td>
      <td class="gpu-title-cell">
        <span class="gpu-name-bold">${o.brand}</span>
        <span class="gpu-subinfo">${o.title}</span>
      </td>
      <td class="text-right">
        <span class="price-cash-highlight">${formatCurrency(o.price_cash)}</span>
        <div class="gpu-subinfo">no PIX</div>
      </td>
      <td class="text-right">
        <span class="price-15x-highlight">15x de ${formatCurrency(inst15xVal)}</span>
        <div class="gpu-subinfo">Total: ${formatCurrency(price15xTotal)}</div>
      </td>
      <td class="text-center font-mono">
        <span style="font-weight:700; color:#c9d1d9;">R$ ${o.cost_per_fps_1440p}</span>
        <div class="gpu-subinfo">115/145 FPS</div>
      </td>
      <td class="text-center font-mono">
        <span style="font-weight:700; color:#38bdf8;">R$ ${o.cost_per_fps_4k}</span>
        <div class="gpu-subinfo">72/92 FPS</div>
      </td>
      <td>
        <div class="score-bar-wrapper">
          <div class="score-bar-bg">
            <div class="score-bar-fill" style="width:${Math.min(100, o.cost_benefit_score)}%;"></div>
          </div>
          <span class="score-num ${o.cost_benefit_score > 75 ? 'text-green' : ''}">${o.cost_benefit_score}</span>
        </div>
      </td>
      <td class="text-center">
        <a href="${o.url}" target="_blank" class="btn btn-secondary" style="padding:6px 12px; font-size:0.8rem;">
          Ver ↗
        </a>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 9. Seção Tecnológica DLSS 5 (Novembro/2026)
function renderDLSS5Section(rec) {
  if (!rec || !rec.dlss5_analysis) return;

  const dlss5 = rec.dlss5_analysis;
  const descEl = document.getElementById('dlss5-main-desc');
  if (descEl && dlss5.description) {
    descEl.innerHTML = dlss5.description.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  }

  const grid = document.getElementById('dlss5-cards-grid');
  if (grid && dlss5.hardware_impact) {
    grid.innerHTML = '';
    dlss5.hardware_impact.forEach(item => {
      const card = document.createElement('div');
      card.className = `dlss5-card-item ${item.model.includes('5070 Ti') ? 'highlight-ti-dlss5' : ''}`;

      card.innerHTML = `
        <div class="dlss5-card-header">
          <h3 class="dlss5-gpu-name">${item.model}</h3>
          <span class="dlss5-badge" style="background:${item.badge_color};">${item.badge}</span>
        </div>

        <div class="dlss5-vram-usage-box">
          <span class="vram-usage-label">Memória & Prontidão:</span>
          <div class="vram-usage-val font-mono">${item.vram_usage}</div>
          <div class="dlss5-readiness-pill">Prontidão: <strong>${item.readiness_score}</strong></div>
        </div>

        <p class="dlss5-summary-text">${item.summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</p>
      `;
      grid.appendChild(card);
    });
  }

  const takeawaysList = document.getElementById('dlss5-takeaways-list');
  if (takeawaysList && dlss5.key_takeaways) {
    takeawaysList.innerHTML = dlss5.key_takeaways.map(t => `<li>${t}</li>`).join('');
  }
}

// 10. Parecer Técnico
function renderVerdict(rec) {
  if (!rec) return;

  document.getElementById('verdict-main-title').textContent = rec.verdict_title || 'Diagnóstico de Escolha';
  document.getElementById('verdict-main-summary').innerHTML = rec.verdict_summary ? rec.verdict_summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') : '';

  const container = document.getElementById('verdict-points-grid');
  if (!container || !rec.detailed_points) return;

  container.innerHTML = '';

  rec.detailed_points.forEach(item => {
    const card = document.createElement('div');
    card.className = 'verdict-item-card';

    const prosHtml = item.pros.map(p => `<li>${p}</li>`).join('');
    const consHtml = item.cons.map(c => `<li>${c}</li>`).join('');

    card.innerHTML = `
      <div class="verdict-item-header">
        <span class="verdict-rank-cat">${item.category}</span>
        <span class="verdict-badge-pill" style="background:${item.badge_color};">${item.badge}</span>
      </div>

      <h3 class="verdict-item-title">${item.model}</h3>
      <div class="verdict-item-price">${item.price_ref}</div>
      <div class="verdict-item-15x" style="font-family:var(--font-mono); font-size:0.85rem; color:#eab308; margin-bottom:8px; font-weight:700;">
        💳 ${item.price_15x || ''}
      </div>
      <div class="verdict-item-fps" style="font-size:0.82rem; color:var(--text-sub); margin-bottom:14px;">
        🎮 1440p: <strong>${item.fps_1440p}</strong> (${item.cost_fps_1440p}) | 🖥️ 4K Nativo: <strong>${item.fps_4k}</strong> (${item.cost_fps_4k})
      </div>
      <p class="verdict-item-text">${item.why_choose}</p>

      <div class="pros-cons-box">
        <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:6px; font-weight:700;">Pontos Fortes:</div>
        <ul class="pros-list" style="margin-bottom:12px;">${prosHtml}</ul>
        
        <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:6px; font-weight:700;">Atenção & Limitações:</div>
        <ul class="cons-list">${consHtml}</ul>
      </div>
    `;
    container.appendChild(card);
  });
}

function formatCurrency(val) {
  if (val === undefined || val === null || isNaN(val)) return 'R$ 0,00';
  return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}


