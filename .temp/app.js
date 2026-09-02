/**
 * GPU Hunter Pro - Frontend Application Logic
 * Foco exclusivo em RTX 5070 e RTX 5070 Ti (Alto Custo-Benefício)
 * Inclui: Top 3 Melhores Opções por Loja, Radar de Promoções por Tempo Limitado e Histórico Diário.
 */

let globalData = null;
let chartCostFps = null;
let chartPerfPrice = null;
let chartDailyHistory = null;
let currentHistoryDays = 30;
let currentTopStoreTab = 'all';
let currentTopModel = 'RTX 5070';

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
  renderTopByStore(data.top_by_store);
  renderLimitedPromos(data.limited_promos);
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
  if (!ctx) return;

  if (chartDailyHistory) {
    chartDailyHistory.destroy();
  }

  const dates = timeline.dates || [];
  const series5070 = timeline.series['RTX 5070']?.min_prices || [];
  const series5070ti = timeline.series['RTX 5070 Ti']?.min_prices || [];

  const formattedLabels = dates.map(d => {
    const parts = d.split('-');
    return `${parts[2]}/${parts[1]}`;
  });

  chartDailyHistory = new Chart(ctx, {
    type: 'line',
    data: {
      labels: formattedLabels,
      datasets: [
        {
          label: 'RTX 5070 (Menor Preço)',
          data: series5070,
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.08)',
          borderWidth: 3,
          pointRadius: dates.length > 30 ? 2 : 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#10B981',
          tension: 0.25,
          fill: true
        },
        {
          label: 'RTX 5070 Ti (Menor Preço)',
          data: series5070ti,
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.06)',
          borderWidth: 3,
          pointRadius: dates.length > 30 ? 2 : 4,
          pointHoverRadius: 6,
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
        intersect: false
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#e6edf3',
            font: { family: 'Outfit', size: 13, weight: '600' },
            boxWidth: 14,
            usePointStyle: true
          }
        },
        tooltip: {
          backgroundColor: '#161b22',
          borderColor: '#30363d',
          borderWidth: 1,
          titleColor: '#fff',
          bodyColor: '#c9d1d9',
          padding: 12,
          callbacks: {
            label: function(ctx) {
              return ` ${ctx.dataset.label}: ${formatCurrency(ctx.parsed.y)}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#8b949e', font: { family: 'Inter', size: 11 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#8b949e',
            font: { family: 'Inter', size: 11 },
            callback: value => `R$ ${(value / 1000).toFixed(1)}k`
          }
        }
      }
    }
  });
}

// 3. Hero / Campeã de Custo-Benefício
function renderChampion(data) {
  const winner = data.winner;
  const stats = data.model_stats['RTX 5070'];
  if (!winner || !stats) return;

  const titleEl = document.getElementById('winner-title');
  const descEl = document.getElementById('winner-desc');
  const priceEl = document.getElementById('winner-price');
  const storeEl = document.getElementById('winner-store');
  const inst15xEl = document.getElementById('winner-15x');
  const costFpsEl = document.getElementById('winner-cost-fps');
  const costFps4kEl = document.getElementById('winner-cost-fps-4k');
  const linkEl = document.getElementById('winner-link');

  if (titleEl) titleEl.textContent = `${stats.best_title || 'NVIDIA GeForce RTX 5070'}`;
  if (descEl) {
    descEl.innerHTML = `
      A <strong>RTX 5070 (12GB GDDR7)</strong> conquistou o 1º lugar geral em eficiência financeira: 
      entrega <strong>115 FPS em 1440p Quad HD</strong> e <strong>72 FPS em 4K Nativo</strong> com o menor custo por quadro gerado do mercado 
      (<strong>R$ ${stats.cost_per_fps_1440p}/FPS em 1440p</strong> e <strong>R$ ${stats.cost_per_fps_4k}/FPS em 4K</strong>). 
      Disponível com arrefecimento superior Triplo Fan (ex: Gainward Python III) por apenas R$ 4.859,99 à vista.
    `;
  }
  if (priceEl) priceEl.textContent = formatCurrency(stats.min_price);
  if (storeEl) storeEl.textContent = `à vista no PIX (${stats.best_store})`;
  if (inst15xEl) inst15xEl.textContent = stats.min_installment_15x_text;
  if (costFpsEl) costFpsEl.textContent = `R$ ${stats.cost_per_fps_1440p} / FPS`;
  if (costFps4kEl) costFps4kEl.textContent = `R$ ${stats.cost_per_fps_4k} / FPS`;
  if (linkEl) linkEl.href = stats.best_url || '#';
}

// 4. NOVA SEÇÃO: TOP 3 MELHORES OPÇÕES POR LOJA
function switchStoreTab(storeKey) {
  currentTopStoreTab = storeKey;
  document.querySelectorAll('.btn-store-tab').forEach(btn => {
    btn.classList.remove('active');
  });
  const activeBtn = document.querySelector(`.btn-store-tab[onclick="switchStoreTab('${storeKey}')"]`);
  if (activeBtn) activeBtn.classList.add('active');
  
  if (globalData && globalData.top_by_store) {
    renderTopByStore(globalData.top_by_store);
  }
}

function switchTopModel(modelName) {
  currentTopModel = modelName;
  document.getElementById('btn-top-5070')?.classList.toggle('active', modelName === 'RTX 5070');
  document.getElementById('btn-top-5070ti')?.classList.toggle('active', modelName === 'RTX 5070 Ti');

  if (globalData && globalData.top_by_store) {
    renderTopByStore(globalData.top_by_store);
  }
}

function renderTopByStore(topByStore) {
  const container = document.getElementById('top-store-container');
  if (!container || !topByStore) return;

  container.innerHTML = '';
  const storesToRender = currentTopStoreTab === 'all' ? ['pichau', 'terabyte', 'kabum'] : [currentTopStoreTab];

  storesToRender.forEach(storeKey => {
    const storeData = topByStore[storeKey];
    if (!storeData) return;

    const offersList = storeData.by_model?.[currentTopModel] || [];
    if (offersList.length === 0) return;

    const column = document.createElement('div');
    column.className = `store-top-column ${storeKey}-theme-column`;

    let cardsHtml = '';
    offersList.forEach(item => {
      const isTripleFan = (item.cooling_type || '').includes('Triplo') || item.title.includes('3X') || item.title.includes('Python III') || item.title.includes('Infinity 3');
      const coolingBadge = isTripleFan ? 
        '<span class="badge-cooling-triple">❄️ Triplo Fan (3 Fans)</span>' : 
        '<span class="badge-cooling-dual">🌬️ Dual Fan (2 Fans)</span>';

      const promoBadge = item.is_limited_promo ? 
        `<span class="badge-promo-live pulse-glow">${item.promo_badge || '⚡ Preço Promocional'}</span>` : 
        '';

      const unitsBadge = item.promo_units_left ? 
        `<span class="badge-units-left">📦 Restam ${item.promo_units_left} un.</span>` : 
        '';

      cardsHtml += `
        <div class="top-rank-card rank-${item.rank_position}">
          <div class="top-rank-card-header">
            <div class="medal-badge medal-pos-${item.rank_position}">
              ${item.rank_label}
            </div>
            <div class="rank-highlight-tag">${item.rank_highlight}</div>
          </div>

          <div class="top-rank-card-body">
            <div class="top-rank-img-wrap">
              <img src="${item.image}" alt="${item.title}" class="top-rank-img" loading="lazy" onerror="this.src='https://media.pichau.com.br/media/catalog/product/cache/74c1057f7991b4edb2bc7bdaa94de933/n/e/ne75070019k9-gb2050t-nac4.jpg'">
            </div>

            <div class="top-rank-details">
              <div class="top-rank-badges-row">
                ${coolingBadge}
                ${promoBadge}
                ${unitsBadge}
              </div>

              <h4 class="top-rank-title" title="${item.title}">${item.title}</h4>

              <div class="top-rank-pricing">
                <div class="top-rank-cash">
                  <span class="cash-label">À VISTA NO PIX:</span>
                  <span class="cash-val">${formatCurrency(item.price_cash)}</span>
                </div>
                <div class="top-rank-installments">
                  <span>${item.installments || '12x no cartão'}</span>
                  <span class="inst-15x-note">ou <strong>15x de ${formatCurrency(item.installment_15x_val)}</strong></span>
                </div>
              </div>

              <div class="top-rank-actions">
                <a href="${item.url}" target="_blank" class="btn btn-primary btn-rank-action">
                  <span>Acessar Oferta na ${storeData.store_name}</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      `;
    });

    column.innerHTML = `
      <div class="store-column-header">
        <div class="store-column-brand">
          <span class="store-big-logo">${storeData.store_logo}</span>
          <span class="store-model-tag">${currentTopModel}</span>
        </div>
        <span class="store-column-sub">Top 3 Melhores Opções Encontradas</span>
      </div>
      <div class="store-column-cards">
        ${cardsHtml}
      </div>
    `;

    container.appendChild(column);
  });
}

// 5. NOVA SEÇÃO: RADAR DE PROMOÇÕES POR TEMPO LIMITADO
function renderLimitedPromos(limitedPromos) {
  const container = document.getElementById('promos-cards-grid');
  const countBadge = document.getElementById('promo-count-badge');
  if (!container) return;

  const promos = limitedPromos || [];
  if (countBadge) {
    countBadge.textContent = `🔥 ${promos.length} Ofertas com Preço Promocional Ativo`;
  }

  container.innerHTML = '';
  if (promos.length === 0) {
    container.innerHTML = '<p style="color:var(--text-muted); padding:20px;">Nenhuma oferta com preço limitado ativa no momento.</p>';
    return;
  }

  promos.slice(0, 6).forEach(p => {
    const card = document.createElement('div');
    card.className = 'promo-radar-card';

    const isTripleFan = (p.cooling_type || '').includes('Triplo') || p.title.includes('3X') || p.title.includes('Python III');
    const coolingTag = isTripleFan ? '<span class="tag-fan-mini">❄️ 3 Fans</span>' : '<span class="tag-fan-mini">🌬️ 2 Fans</span>';
    const discountTag = p.promo_discount_pct ? `<span class="tag-disc-mini">-${p.promo_discount_pct}%</span>` : '';

    card.innerHTML = `
      <div class="promo-radar-top">
        <span class="promo-radar-store">${p.store_logo || p.store}</span>
        <span class="promo-radar-badge pulse-glow">${p.promo_badge || '⚡ OFERTA LIMITADA'}</span>
      </div>

      <div class="promo-radar-middle">
        <img src="${p.image}" alt="${p.title}" class="promo-radar-thumb" onerror="this.src='https://media.pichau.com.br/media/catalog/product/cache/74c1057f7991b4edb2bc7bdaa94de933/n/e/ne75070019k9-gb2050t-nac4.jpg'">
        <div class="promo-radar-info">
          <div class="promo-radar-tags">${coolingTag} ${discountTag}</div>
          <h5 class="promo-radar-title">${p.title}</h5>
          <div class="promo-radar-prices">
            <span class="promo-radar-cash">${formatCurrency(p.price_cash)}</span>
            <span class="promo-radar-sub">no PIX</span>
          </div>
        </div>
      </div>

      <div class="promo-radar-bottom">
        <span class="promo-radar-inst">15x de ${formatCurrency(p.installment_15x_val)}</span>
        <a href="${p.url}" target="_blank" class="btn btn-sm btn-primary">Ir p/ Loja ↗</a>
      </div>
    `;

    container.appendChild(card);
  });
}

// 6. Comparativo dos Modelos (5070 vs 5070 Ti)
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
    card.className = `model-card ${isChampion ? 'champion-border' : 'enthusiast-border'}`;

    card.innerHTML = `
      <div class="model-card-header">
        <div class="model-badge ${isChampion ? 'badge-champion' : 'badge-4k'}">
          ${isChampion ? '🥇 MELHOR CUSTO X BENEFÍCIO' : '🥈 CAMPEÃ 4K NATIVO (16GB)'}
        </div>
        <h3 class="model-title">${modelName}</h3>
        <p class="model-tier-sub">${isChampion ? '1440p Ultra High Refresh / 4K DLSS' : '4K Ultra Nativo + Imunidade de VRAM'}</p>
      </div>

      <div class="model-pricing-highlight">
        <div class="price-main">${formatCurrency(st.min_price)} <span class="price-type">à vista (PIX)</span></div>
        <div class="price-15x-box">
          <span class="inst-pill">15x de ${formatCurrency(st.min_installment_15x_val)}</span>
          <span class="inst-total-note">Total ${formatCurrency(st.min_price_15x_total)} (+10% juros)</span>
        </div>
        <div class="best-offer-link-box">
          <span style="font-size:0.8rem; color:var(--text-muted);">Menor preço na loja:</span>
          <a href="${st.best_url}" target="_blank" class="store-mini-link">
            ${st.best_store} - ${st.best_title.substring(0, 42)}... ↗
          </a>
        </div>
      </div>

      <div class="model-specs-list">
        <div class="spec-row">
          <span class="spec-name">Memória VRAM:</span>
          <span class="spec-val font-mono">${st.vram}</span>
        </div>
        <div class="spec-row">
          <span class="spec-name">Consumo Térmico (TDP):</span>
          <span class="spec-val font-mono">${st.tdp}</span>
        </div>
        <div class="spec-row">
          <span class="spec-name">Desempenho 1440p:</span>
          <span class="spec-val font-mono">${st.avg_fps_1440p} FPS Médio</span>
        </div>
        <div class="spec-row">
          <span class="spec-name">Desempenho 4K Nativo:</span>
          <span class="spec-val font-mono">${st.avg_fps_4k} FPS Médio</span>
        </div>
        <div class="spec-row">
          <span class="spec-name">Custo / FPS em 1440p:</span>
          <span class="spec-val font-mono text-green">R$ ${st.cost_per_fps_1440p} / FPS</span>
        </div>
        <div class="spec-row">
          <span class="spec-name">Custo / FPS em 4K:</span>
          <span class="spec-val font-mono text-accent">R$ ${st.cost_per_fps_4k} / FPS</span>
        </div>
      </div>

      <div class="model-card-footer">
        <a href="${st.best_url}" target="_blank" class="btn btn-block ${isChampion ? 'btn-primary' : 'btn-secondary'}">
          Comprar na ${st.best_store} ↗
        </a>
      </div>
    `;

    container.appendChild(card);
  });
}

// 7. Simulador de Parcelamento em 15x
function renderSimulator15x(modelStats, rec) {
  const container = document.getElementById('sim-15x-cards-grid');
  if (!container || !modelStats) return;

  const st5070 = modelStats['RTX 5070'];
  const st5070ti = modelStats['RTX 5070 Ti'];
  if (!st5070 || !st5070ti) return;

  const diffCash = st5070ti.min_price - st5070.min_price;
  const diff15x = st5070ti.min_installment_15x_val - st5070.min_installment_15x_val;

  container.innerHTML = `
    <div class="sim-15x-option-card winner-sim-card">
      <div class="sim-card-badge">OPÇÃO MAIS ACESSÍVEL (15x)</div>
      <div class="sim-card-header">
        <h3>RTX 5070 (12GB)</h3>
        <span class="sim-store-note">a partir de ${formatCurrency(st5070.min_price)} à vista</span>
      </div>

      <div class="sim-monthly-big">
        <span class="sim-currency">R$</span>
        <span class="sim-number">${Math.floor(st5070.min_installment_15x_val)}</span>
        <span class="sim-cents">,${(st5070.min_installment_15x_val % 1).toFixed(2).substring(2)}</span>
        <span class="sim-per-month">/ mês em 15x</span>
      </div>

      <p class="sim-math-desc">
        Total parcelado: <strong>${formatCurrency(st5070.min_price_15x_total)}</strong> (preço a prazo +10% de acréscimo médio de 15 parcelas).
      </p>

      <ul class="sim-benefit-list">
        <li>✔ Menor prestação mensal: apenas ~R$ ${Math.round(st5070.min_installment_15x_val)}/mês</li>
        <li>✔ 115 FPS em 1440p Quad HD com DLSS 4</li>
        <li>✔ 72 FPS sólidos em 4K Nativo</li>
        <li>✔ Economia de ${formatCurrency(diffCash)} à vista vs 5070 Ti</li>
      </ul>

      <a href="${st5070.best_url}" target="_blank" class="btn btn-block btn-primary">
        Ver Melhor Oferta (15x) ↗
      </a>
    </div>

    <div class="sim-15x-option-card">
      <div class="sim-card-badge badge-blue">UPGRADE MÁXIMO 4K (16GB)</div>
      <div class="sim-card-header">
        <h3>RTX 5070 Ti (16GB)</h3>
        <span class="sim-store-note">a partir de ${formatCurrency(st5070ti.min_price)} à vista</span>
      </div>

      <div class="sim-monthly-big text-accent">
        <span class="sim-currency">R$</span>
        <span class="sim-number">${Math.floor(st5070ti.min_installment_15x_val)}</span>
        <span class="sim-cents">,${(st5070ti.min_installment_15x_val % 1).toFixed(2).substring(2)}</span>
        <span class="sim-per-month">/ mês em 15x</span>
      </div>

      <p class="sim-math-desc">
        Total parcelado: <strong>${formatCurrency(st5070ti.min_price_15x_total)}</strong> (+R$ ${diff15x.toFixed(2)}/mês a mais que a 5070).
      </p>

      <ul class="sim-benefit-list">
        <li>✔ 16GB GDDR7 + Barramento 256-bit (896 GB/s)</li>
        <li>✔ 92 FPS em 4K Nativo Ultra (+28% de performance)</li>
        <li>✔ Imunidade total à falta de VRAM até 2030+</li>
        <li>✔ Custa +R$ ${Math.round(diff15x)}/mês na parcela em 15x</li>
      </ul>

      <a href="${st5070ti.best_url}" target="_blank" class="btn btn-block btn-secondary">
        Ver Melhor Oferta (15x) ↗
      </a>
    </div>
  `;
}

// 8. Gráficos Comparativos
function renderCharts(modelStats) {
  if (!modelStats) return;
  const labels = ['RTX 5070', 'RTX 5070 Ti'];

  // Gráfico 1: R$ por FPS
  const ctxCost = document.getElementById('chart-cost-fps');
  if (ctxCost) {
    if (chartCostFps) chartCostFps.destroy();
    chartCostFps = new Chart(ctxCost, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Custo por FPS em 1440p (R$/FPS)',
            data: [modelStats['RTX 5070'].cost_per_fps_1440p, modelStats['RTX 5070 Ti'].cost_per_fps_1440p],
            backgroundColor: 'rgba(16, 185, 129, 0.85)',
            borderColor: '#10B981',
            borderWidth: 1,
            borderRadius: 6
          },
          {
            label: 'Custo por FPS em 4K Nativo (R$/FPS)',
            data: [modelStats['RTX 5070'].cost_per_fps_4k, modelStats['RTX 5070 Ti'].cost_per_fps_4k],
            backgroundColor: 'rgba(56, 189, 248, 0.85)',
            borderColor: '#38bdf8',
            borderWidth: 1,
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#c9d1d9', font: { family: 'Outfit', size: 12 } } },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.dataset.label}: R$ ${ctx.parsed.y.toFixed(2)} por frame`
            }
          }
        },
        scales: {
          x: { ticks: { color: '#8b949e', font: { family: 'Outfit', weight: '600' } } },
          y: {
            ticks: { color: '#8b949e', callback: v => `R$ ${v}` },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          }
        }
      }
    });
  }

  // Gráfico 2: Desempenho vs Preço
  const ctxPerf = document.getElementById('chart-perf-price');
  if (ctxPerf) {
    if (chartPerfPrice) chartPerfPrice.destroy();
    chartPerfPrice = new Chart(ctxPerf, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'FPS Médio 1440p',
            data: [modelStats['RTX 5070'].avg_fps_1440p, modelStats['RTX 5070 Ti'].avg_fps_1440p],
            backgroundColor: 'rgba(16, 185, 129, 0.7)',
            borderRadius: 6
          },
          {
            label: 'FPS Médio 4K Nativo',
            data: [modelStats['RTX 5070'].avg_fps_4k, modelStats['RTX 5070 Ti'].avg_fps_4k],
            backgroundColor: 'rgba(56, 189, 248, 0.7)',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#c9d1d9', font: { family: 'Outfit', size: 12 } } },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y} FPS`
            }
          }
        },
        scales: {
          x: { ticks: { color: '#8b949e', font: { family: 'Outfit', weight: '600' } } },
          y: {
            ticks: { color: '#8b949e', callback: v => `${v} FPS` },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          }
        }
      }
    });
  }
}

// 9. Simulador de Orçamento
function updateBudgetSimulation() {
  const slider = document.getElementById('budget-slider');
  const display = document.getElementById('budget-value-display');
  const resultBox = document.getElementById('sim-result-box');
  if (!slider || !globalData || !globalData.model_stats) return;

  const budget = parseFloat(slider.value);
  display.textContent = formatCurrency(budget);

  const stats = globalData.model_stats;
  const p5070 = stats['RTX 5070']?.min_price || 4859.99;
  const p5070ti = stats['RTX 5070 Ti']?.min_price || 7899.99;
  const inst5070 = stats['RTX 5070']?.min_installment_15x_val || 419.29;
  const inst5070ti = stats['RTX 5070 Ti']?.min_installment_15x_val || 681.45;

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
    recommendedModel = 'NVIDIA GeForce RTX 5070 (12GB Triplo Fan)';
    leftover = budget - p5070;
    neededForNext = p5070ti - budget;
    instEquivalent = `Ou parcele em 15x de ${formatCurrency(inst5070)}/mês`;
    tip = `Campeã de Custo x Benefício! A Gainward Python III Triplo Fan roda 4K Nativo a 72 FPS e 1440p Ultra com folga. Sobram ${formatCurrency(leftover)} no bolso.`;
  } else {
    recommendedModel = 'Orçamento Abaixo do Valor à Vista';
    neededForNext = p5070 - budget;
    instEquivalent = `Você pode parcelar a 5070 em 15x de ${formatCurrency(inst5070)}/mês!`;
    tip = `A placa mais em conta com 3 fans (Gainward Python III) custa ${formatCurrency(p5070)} à vista. Se preferir parcelar em 15x com +10% de acréscimo, a prestação fica em apenas ${formatCurrency(inst5070)}/mês.`;
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

// 10. Tabela Geral de Ofertas com Filtros de Promoção e Fans
function renderOffersTable() {
  if (!globalData || !globalData.offers) return;

  const tbody = document.getElementById('offers-tbody');
  const countLabel = document.getElementById('offers-count-label');
  const filterModel = document.getElementById('filter-model').value;
  const filterStore = document.getElementById('filter-store').value;
  const filterPromo = document.getElementById('filter-promo')?.value || 'ALL';
  const filterPayment = document.getElementById('filter-payment').value;
  const filterSort = document.getElementById('filter-sort').value;

  let offers = [...globalData.offers];

  if (filterModel !== 'ALL') {
    offers = offers.filter(o => o.gpu_model === filterModel);
  }

  if (filterStore !== 'ALL') {
    offers = offers.filter(o => o.store_key === filterStore);
  }

  if (filterPromo === 'promo_only') {
    offers = offers.filter(o => o.is_limited_promo);
  } else if (filterPromo === 'triple_only') {
    offers = offers.filter(o => (o.cooling_type || '').includes('Triplo') || o.title.includes('3X') || o.title.includes('Python III') || o.title.includes('Infinity 3'));
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

    const isTripleFan = (o.cooling_type || '').includes('Triplo') || o.title.includes('3X') || o.title.includes('Python III') || o.title.includes('Infinity 3');
    const fanTag = isTripleFan ? '<span class="tag-cooling-inline triple">❄️ 3 Fans</span>' : '<span class="tag-cooling-inline dual">🌬️ 2 Fans</span>';
    const promoTag = o.is_limited_promo ? `<span class="tag-promo-inline pulse-glow">${o.promo_badge || '⚡ Promoção'}</span>` : '';

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
      <td>
        <div class="cooling-promo-cell">
          ${fanTag}
          ${promoTag}
        </div>
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

// 11. Seção Tecnológica DLSS 5 (Novembro/2026)
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

// 12. Parecer Técnico
function renderVerdict(rec) {
  if (!rec) return;

  document.getElementById('verdict-main-title').textContent = rec.verdict_title || 'Diagnóstico de Escolha';
  document.getElementById('verdict-main-summary').innerHTML = rec.verdict_summary ? rec.verdict_summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') : '';

  const container = document.getElementById('verdict-points-grid');
  if (!container || !rec.detailed_points) return;

  container.innerHTML = '';

  rec.detailed_points.forEach(pt => {
    const card = document.createElement('div');
    card.className = 'verdict-point-card';

    let prosList = pt.pros.map(p => `<li><span class="pro-icon">✔</span> ${p}</li>`).join('');
    let consList = pt.cons.map(c => `<li><span class="con-icon">✖</span> ${c}</li>`).join('');

    card.innerHTML = `
      <div class="verdict-point-header">
        <span class="verdict-category-badge" style="background:${pt.badge_color};">${pt.badge}</span>
        <h3 class="verdict-model-title">${pt.model}</h3>
        <div class="verdict-price-tag">${pt.price_ref}</div>
        <div class="verdict-15x-tag">${pt.price_15x}</div>
      </div>

      <div class="verdict-point-body">
        <div class="verdict-metrics-row">
          <div class="verdict-metric-item">
            <span class="v-label">FPS 1440p Ultra:</span>
            <span class="v-val font-mono">${pt.fps_1440p}</span>
          </div>
          <div class="verdict-metric-item">
            <span class="v-label">FPS 4K Nativo:</span>
            <span class="v-val font-mono">${pt.fps_4k}</span>
          </div>
        </div>

        <p class="verdict-why-text">${pt.why_choose}</p>

        <div class="pros-cons-grid">
          <div class="pros-box">
            <h4>Pontos Fortes:</h4>
            <ul>${prosList}</ul>
          </div>
          <div class="cons-box">
            <h4>Considerações:</h4>
            <ul>${consList}</ul>
          </div>
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

function formatCurrency(val) {
  if (val === undefined || val === null || isNaN(val)) return 'R$ 0,00';
  return Number(val).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}
