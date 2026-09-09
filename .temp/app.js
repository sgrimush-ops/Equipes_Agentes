/**
 * GPU Hunter Pro - Frontend Application Logic
 * Foco exclusivo na NVIDIA GeForce RTX 5070 Ti (16GB GDDR7)
 * Prioridade: Parcelamento Sem Juros (10x vs 12x), Menor Parcela Mensal e Preço Total Sem Juros.
 */

let globalData = null;
let chartCostFps = null;
let chartPerfPrice = null;
let chartDailyHistory = null;
let currentHistoryDays = 30;
let currentTopStoreTab = 'all';

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
      statusText.innerHTML = '<span style="color:#38bdf8;">Varrendo cotações sem juros ao vivo...</span>';
      if (btnRefresh) btnRefresh.disabled = true;
    } else {
      statusText.textContent = 'Monitorando Parcelamento Sem Juros (RTX 5070 Ti)';
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
    alert('Varredura ao vivo iniciada para RTX 5070 Ti nas 3 lojas (foco sem juros). O snapshot do dia será atualizado!');
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
  renderModelsGrid(data.model_stats, data.offers);
  renderSimulatorInterestFree(data.recommendation, data.model_stats);
  renderCharts(data.model_stats, data.offers);
  renderOffersTable();
  renderDLSS5Section(data.recommendation);
  renderVerdict(data.recommendation);
  updateBudgetSimulation();
}

// 1. Ticker de Oscilação Diária do Preço Total Sem Juros e Parcela
function renderTickerCards(variations) {
  const container = document.getElementById('ticker-cards-grid');
  if (!container || !variations) return;

  container.innerHTML = '';
  const models = ['RTX 5070 Ti'];

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

    const minInst = v.min_installment_val ? formatCurrency(v.min_installment_val) : 'R$ 774,51';

    card.innerHTML = `
      <div class="ticker-card-top">
        <h3 class="ticker-model-name">${model} (16GB GDDR7)</h3>
        ${v.is_at_all_time_low ? '<span class="all-time-low-tag">🏷️ MENOR PREÇO HISTÓRICO</span>' : ''}
      </div>

      <div class="ticker-price-main">${formatCurrency(v.current_min_price)} <span style="font-size:0.85rem; color:var(--text-muted); font-weight:400;">(Total Sem Juros)</span></div>
      <div style="font-size:1.05rem; font-weight:700; color:var(--accent-green); margin-top:2px; margin-bottom:8px;">
        💳 Parcela Mínima: 12x de ${minInst} <span style="font-size:0.75rem; font-weight:400; color:var(--text-muted);">sem juros</span>
      </div>

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
        <span>Maior Total: ${formatCurrency(v.all_time_high)}</span>
      </div>
    `;

    container.appendChild(card);
  });
}

// 2. Gráfico do Histórico Diário de Preços Total a Prazo Sem Juros
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
  const series5070ti = timeline.series['RTX 5070 Ti']?.min_prices || [];
  const avg5070ti = timeline.series['RTX 5070 Ti']?.avg_prices || [];

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
          label: 'RTX 5070 Ti (Menor Preço Total Sem Juros)',
          data: series5070ti,
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.12)',
          borderWidth: 3,
          pointRadius: dates.length > 30 ? 2 : 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#38bdf8',
          tension: 0.25,
          fill: true
        },
        {
          label: 'Média de Mercado (Preço a Prazo Sem Juros)',
          data: avg5070ti,
          borderColor: '#818cf8',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [5, 5],
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.25,
          fill: false
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

// 3. Hero / Campeã de Menor Parcela Sem Juros
function renderChampion(data) {
  const winner = data.winner;
  const stats = data.model_stats['RTX 5070 Ti'];
  if (!winner || !stats) return;

  const titleEl = document.getElementById('winner-title');
  const descEl = document.getElementById('winner-desc');
  const instEl = document.getElementById('winner-installment');
  const storeEl = document.getElementById('winner-store');
  const totalEl = document.getElementById('winner-total');
  const costFpsEl = document.getElementById('winner-cost-fps');
  const costFps4kEl = document.getElementById('winner-cost-fps-4k');
  const linkEl = document.getElementById('winner-link');

  if (titleEl) titleEl.textContent = `${winner.title || stats.best_title || 'NVIDIA GeForce RTX 5070 Ti (16GB GDDR7)'}`;
  if (descEl) {
    descEl.innerHTML = `
      A <strong>${winner.title || stats.best_title || 'RTX 5070 Ti (16GB GDDR7)'}</strong> na <strong>${winner.store}</strong> é o grande destaque de acessibilidade financeira: 
      permite parcelar em <strong>${winner.installments_text}</strong>, com valor total de <strong>${formatCurrency(winner.price_card || stats.min_price_card)}</strong>.
      Com <strong>16GB de VRAM GDDR7</strong> a 896 GB/s, entrega <strong>92 FPS em 4K Nativo</strong> e <strong>145 FPS em 1440p</strong> com custo total de apenas 
      <strong>R$ ${stats.cost_per_fps_4k}/FPS em 4K</strong>.
    `;
  }
  if (instEl) instEl.textContent = winner.installments_text || stats.min_installment_text;
  if (storeEl) storeEl.textContent = `sem juros na ${winner.store || stats.best_store}`;
  if (totalEl) totalEl.textContent = formatCurrency(winner.price_card || stats.min_price_card);
  if (costFpsEl) costFpsEl.textContent = `R$ ${winner.cost_per_fps_1440p || stats.cost_per_fps_1440p} / FPS Total`;
  if (costFps4kEl) costFps4kEl.textContent = `R$ ${winner.cost_per_fps_4k || stats.cost_per_fps_4k} / FPS Total`;
  if (linkEl) linkEl.href = winner.url || stats.best_url || '#';
}

// 4. TOP 3 MELHORES OPÇÕES POR LOJA (PARCELAMENTO SEM JUROS)
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

function renderTopByStore(topByStore) {
  const container = document.getElementById('top-store-container');
  if (!container || !topByStore) return;

  container.innerHTML = '';
  const storesToRender = currentTopStoreTab === 'all' ? ['kabum', 'pichau', 'terabyte'] : [currentTopStoreTab];

  storesToRender.forEach(storeKey => {
    const storeData = topByStore[storeKey];
    if (!storeData) return;

    const offersList = storeData.by_model?.['RTX 5070 Ti'] || [];

    const column = document.createElement('div');
    column.className = `store-top-column ${storeKey}-theme-column`;

    let cardsHtml = '';

    if (offersList.length === 0) {
      const searchUrl = storeKey === 'terabyte' ? 
        'https://www.terabyteshop.com.br/busca?str=RTX+5070+Ti' : 
        (storeKey === 'pichau' ? 'https://www.pichau.com.br/search?q=RTX%205070%20Ti' : 'https://www.kabum.com.br/busca/rtx-5070-ti');

      cardsHtml = `
        <div class="store-empty-notice" style="padding: 24px 16px; text-align: center; background: rgba(255,255,255,0.02); border-radius: 12px; border: 1px dashed rgba(255,255,255,0.12); margin-top: 8px;">
          <div style="font-size: 2.2rem; margin-bottom: 8px;">📦</div>
          <h4 style="font-size: 1rem; color: #f59e0b; margin-bottom: 6px; font-weight: 600;">Lotes Esgotados no Momento</h4>
          <p style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.4; margin-bottom: 14px;">
            A <strong>${storeData.store_name}</strong> está sem estoque ativo da RTX 5070 Ti no momento. O robô varre o catálogo a cada minuto e reativará os rankings em ${storeData.installments_mode} assim que a distribuidora liberar o novo lote.
          </p>
          <a href="${searchUrl}" target="_blank" class="btn btn-secondary" style="font-size: 0.8rem; padding: 6px 12px; display: inline-flex; align-items: center; gap: 6px;">
            <span>🔍 Acompanhar Reposição na Loja</span>
          </a>
        </div>
      `;
    } else {
      offersList.forEach(item => {
        const isTripleFan = (item.cooling_type || '').includes('Triplo') || item.title.includes('3X') || item.title.includes('Solid') || item.title.includes('GamingPro');
        const coolingBadge = isTripleFan ? 
          '<span class="badge-cooling-triple">❄️ Triplo Fan (3 Fans)</span>' : 
          '<span class="badge-cooling-dual">🌬️ Dual Fan (2 Fans)</span>';

        const promoBadge = item.is_limited_promo ? 
          `<span class="badge-promo-live pulse-glow">${item.promo_badge || '⚡ Preço Promocional'}</span>` : 
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
                <img src="${item.image}" alt="${item.title}" class="top-rank-img" loading="lazy" onerror="this.src='https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg'">
              </div>

              <div class="top-rank-details">
                <div class="top-rank-badges-row">
                  ${coolingBadge}
                  ${promoBadge}
                  <span style="font-size:0.7rem; background:rgba(16, 185, 129, 0.15); color:#10B981; padding:2px 6px; border-radius:4px; font-weight:600;">🔗 Link Direto com Estoque</span>
                </div>

                <h4 class="top-rank-title" title="${item.title}">${item.title}</h4>

                <div class="top-rank-pricing">
                  <div class="top-rank-cash">
                    <span class="cash-label">PARCELA SEM JUROS:</span>
                    <span class="cash-val" style="color:var(--accent-green);">${item.installments_text}</span>
                  </div>
                  <div class="top-rank-installments">
                    <span>Total Sem Juros: <strong>${formatCurrency(item.price_card)}</strong></span>
                    <span class="inst-15x-note">Custo Total: R$ ${item.cost_per_fps_4k}/FPS em 4K</span>
                  </div>
                </div>

                <div class="top-rank-actions">
                  <a href="${item.url}" target="_blank" class="btn btn-primary btn-rank-action">
                    <span>Acessar Placa na Loja (${storeData.installments_mode})</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                  </a>
                </div>
              </div>
            </div>
          </div>
        `;
      });
    }

    column.innerHTML = `
      <div class="store-column-header">
        <div class="store-column-brand">
          <span class="store-big-logo">${storeData.store_logo}</span>
          <span class="store-model-tag">${storeData.installments_mode}</span>
        </div>
        <span class="store-column-sub">${offersList.length > 0 ? 'Top Melhores Opções em Estoque' : 'Estoque Indisponível no Momento'}</span>
      </div>
      <div class="store-column-cards">
        ${cardsHtml}
      </div>
    `;

    container.appendChild(column);
  });
}

// 5. Visão Geral de Modelos da RTX 5070 Ti
function renderModelsGrid(modelStats, offers) {
  const container = document.getElementById('models-grid');
  if (!container || !modelStats) return;

  const st = modelStats['RTX 5070 Ti'];
  if (!st) return;

  container.innerHTML = `
    <div class="model-card enthusiast-border" style="grid-column: 1 / -1;">
      <div class="model-card-header">
        <div class="model-badge badge-4k">
          👑 SWEET SPOT 4K NATIVO • PARCELAMENTO SEM JUROS (16GB GDDR7)
        </div>
        <h3 class="model-title">NVIDIA GeForce RTX 5070 Ti</h3>
        <p class="model-tier-sub">Arquitetura Blackwell • 16GB GDDR7 • 256-bit (896 GB/s) • 300W TDP</p>
      </div>

      <div class="model-pricing-highlight">
        <div class="price-main">${formatCurrency(st.min_price_card)} <span class="price-type">Total a Prazo Sem Juros</span></div>
        <div class="price-15x-box">
          <span class="inst-pill" style="background:rgba(16, 185, 129, 0.2); border:1px solid #10b981; color:#10b981;">
            💳 Menor Parcela: 12x de ${formatCurrency(st.min_installment_val)} sem juros
          </span>
          <span class="inst-total-note">Disponível na Pichau (12x) e TerabyteShop (12x)</span>
        </div>
        <div class="best-offer-link-box">
          <span style="font-size:0.8rem; color:var(--text-muted);">Menor parcela encontrada:</span>
          <a href="${st.best_url}" target="_blank" class="store-mini-link">
            ${st.best_store} - ${st.best_title.substring(0, 50)}... ↗
          </a>
        </div>
      </div>

      <div class="model-specs-list" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:12px;">
        <div class="spec-row">
          <span class="spec-name">Memória VRAM:</span>
          <span class="spec-val font-mono">${st.vram}</span>
        </div>
        <div class="spec-row">
          <span class="spec-name">Consumo Térmico (TDP):</span>
          <span class="spec-val font-mono">${st.tdp}</span>
        </div>
        <div class="spec-row">
          <span class="spec-name">Desempenho 1440p Ultra:</span>
          <span class="spec-val font-mono">${st.avg_fps_1440p} FPS Médio</span>
        </div>
        <div class="spec-row">
          <span class="spec-name">Desempenho 4K Nativo:</span>
          <span class="spec-val font-mono">${st.avg_fps_4k} FPS Médio</span>
        </div>
        <div class="spec-row">
          <span class="spec-name">Custo Total / FPS (1440p):</span>
          <span class="spec-val font-mono text-green">R$ ${st.cost_per_fps_1440p} / FPS</span>
        </div>
        <div class="spec-row">
          <span class="spec-name">Custo Total / FPS (4K):</span>
          <span class="spec-val font-mono text-accent">R$ ${st.cost_per_fps_4k} / FPS</span>
        </div>
      </div>

      <div class="model-card-footer" style="margin-top:16px;">
        <a href="${st.best_url}" target="_blank" class="btn btn-block btn-primary">
          Acessar Oferta em 12x Sem Juros (${st.best_store}) ↗
        </a>
      </div>
    </div>
  `;
}

// 6. Análise Financeira: Comparativo 10x vs 12x Sem Juros
function renderSimulatorInterestFree(rec, modelStats) {
  const container = document.getElementById('sim-interest-free-grid');
  if (!container || !rec) return;

  const pInst = rec.pichau_inst || 774.51;
  const kInst = rec.kabum_inst || 929.41;
  const tInst = rec.terabyte_inst || 813.63;
  const diffKP = rec.diff_monthly_kabum_pichau || 154.90;

  container.innerHTML = `
    <!-- Card 1: Pichau (12x Sem Juros) -->
    <div class="sim-15x-option-card winner-sim-card">
      <div class="sim-card-badge">🥇 MENOR IMPACTO NA RENDA</div>
      <div class="sim-card-header">
        <h3>Pichau (12x Sem Juros)</h3>
        <span class="sim-store-note">Zotac Solid SFF Triplo Fan</span>
      </div>

      <div class="sim-monthly-big text-green">
        <span class="sim-currency">R$</span>
        <span class="sim-number">${Math.floor(pInst)}</span>
        <span class="sim-cents">,${(pInst % 1).toFixed(2).substring(2)}</span>
        <span class="sim-per-month">/ mês em 12x</span>
      </div>

      <p class="sim-math-desc">
        Total a prazo: <strong>R$ 9.294,11 sem juros</strong>.<br>
        <span style="color:#10b981; font-weight:600;">Economia de R$ ${diffKP.toFixed(2)}/mês no seu fluxo de caixa vs KaBuM!</span>
      </p>

      <ul class="sim-benefit-list">
        <li>✔ 12 parcelas sem juros no cartão de crédito</li>
        <li>✔ Menor prestação mensal entre todas as lojas</li>
        <li>✔ Dissipador com 3 Fans e excelente fluxo térmico</li>
        <li>✔ 16GB GDDR7 e 92 FPS sólidos em 4K nativo</li>
      </ul>

      <a href="https://www.pichau.com.br" target="_blank" class="btn btn-block btn-primary">
        Ver Opções 12x na Pichau ↗
      </a>
    </div>

    <!-- Card 2: TerabyteShop (12x Sem Juros) -->
    <div class="sim-15x-option-card">
      <div class="sim-card-badge badge-blue">🥈 2ª MELHOR PARCELA (12X)</div>
      <div class="sim-card-header">
        <h3>TerabyteShop (12x Sem Juros)</h3>
        <span class="sim-store-note">Gainward Phoenix Triplo Fan</span>
      </div>

      <div class="sim-monthly-big text-accent">
        <span class="sim-currency">R$</span>
        <span class="sim-number">${Math.floor(tInst)}</span>
        <span class="sim-cents">,${(tInst % 1).toFixed(2).substring(2)}</span>
        <span class="sim-per-month">/ mês em 12x</span>
      </div>

      <p class="sim-math-desc">
        Total a prazo: <strong>R$ 9.763,53 sem juros</strong>.<br>
        Excelente construção e iluminação ARGB sincronizada.
      </p>

      <ul class="sim-benefit-list">
        <li>✔ 12 parcelas sem juros no cartão</li>
        <li>✔ Parcela contida de R$ 813,63/mês</li>
        <li>✔ Edição Phoenix com backplate de metal reforçado</li>
        <li>✔ Duplo rolamento nas ventoinhas para durabilidade</li>
      </ul>

      <a href="https://www.terabyteshop.com.br" target="_blank" class="btn btn-block btn-secondary">
        Ver Opções 12x na Terabyte ↗
      </a>
    </div>

    <!-- Card 3: KaBuM! (10x Sem Juros) -->
    <div class="sim-15x-option-card">
      <div class="sim-card-badge" style="background:rgba(249, 115, 22, 0.2); border:1px solid #f97316; color:#f97316;">🥉 QUITAÇÃO EM 10 MESES</div>
      <div class="sim-card-header">
        <h3>KaBuM! (10x Sem Juros)</h3>
        <span class="sim-store-note">Palit GamingPro-S Triplo Fan</span>
      </div>

      <div class="sim-monthly-big text-yellow">
        <span class="sim-currency">R$</span>
        <span class="sim-number">${Math.floor(kInst)}</span>
        <span class="sim-cents">,${(kInst % 1).toFixed(2).substring(2)}</span>
        <span class="sim-per-month">/ mês em 10x</span>
      </div>

      <p class="sim-math-desc">
        Total a prazo: <strong>R$ 9.294,11 sem juros</strong>.<br>
        Mesmo valor total da Pichau, mas dividido em 10x (+R$ 154,90/mês).
      </p>

      <ul class="sim-benefit-list">
        <li>✔ Quitação 2 meses antes (10 meses vs 12 meses)</li>
        <li>✔ Mesmo total final de R$ 9.294,11</li>
        <li>✔ Exige maior margem no salário a cada mês</li>
        <li>✔ Palit GamingPro-S com 3 fans e Dual BIOS</li>
      </ul>

      <a href="https://www.kabum.com.br" target="_blank" class="btn btn-block btn-ghost">
        Ver Opções 10x na KaBuM! ↗
      </a>
    </div>
  `;
}

// 7. Gráficos Comparativos: Custo por FPS Total e Preço Total vs Parcela
function renderCharts(modelStats, offers) {
  if (!offers || offers.length === 0) return;

  const topOffers = offers.slice(0, 5);
  const labels = topOffers.map(o => `${o.brand} (${o.store})`);
  const cost4kData = topOffers.map(o => o.cost_per_fps_4k);
  const cost1440pData = topOffers.map(o => o.cost_per_fps_1440p);
  const cardPrices = topOffers.map(o => o.price_card);
  const instVals = topOffers.map(o => o.installment_val);

  // Gráfico 1: Custo Total por FPS
  const ctxCost = document.getElementById('chart-cost-fps');
  if (ctxCost) {
    if (chartCostFps) chartCostFps.destroy();
    chartCostFps = new Chart(ctxCost, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Custo Total por FPS em 1440p (R$/FPS)',
            data: cost1440pData,
            backgroundColor: 'rgba(16, 185, 129, 0.85)',
            borderColor: '#10B981',
            borderWidth: 1,
            borderRadius: 6
          },
          {
            label: 'Custo Total por FPS em 4K (R$/FPS)',
            data: cost4kData,
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

  // Gráfico 2: Preço Total Sem Juros vs Parcela Mensal
  const ctxPerf = document.getElementById('chart-perf-price');
  if (ctxPerf) {
    if (chartPerfPrice) chartPerfPrice.destroy();
    chartPerfPrice = new Chart(ctxPerf, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Preço Total Sem Juros (R$)',
            data: cardPrices,
            backgroundColor: 'rgba(56, 189, 248, 0.75)',
            borderRadius: 6,
            yAxisID: 'y'
          },
          {
            label: 'Parcela Mensal Sem Juros (R$/mês)',
            data: instVals,
            backgroundColor: 'rgba(16, 185, 129, 0.85)',
            borderRadius: 6,
            yAxisID: 'y1'
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
              label: ctx => ` ${ctx.dataset.label}: ${formatCurrency(ctx.parsed.y)}`
            }
          }
        },
        scales: {
          x: { ticks: { color: '#8b949e', font: { family: 'Outfit', weight: '600' } } },
          y: {
            type: 'linear',
            position: 'left',
            ticks: { color: '#38bdf8', callback: v => `R$ ${(v/1000).toFixed(1)}k` },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          y1: {
            type: 'linear',
            position: 'right',
            ticks: { color: '#10b981', callback: v => `R$ ${v}` },
            grid: { drawOnChartArea: false }
          }
        }
      }
    });
  }
}

// 8. Simulador de Capacidade de Parcela Mensal
function updateBudgetSimulation() {
  const slider = document.getElementById('budget-slider');
  const display = document.getElementById('budget-value-display');
  const resultBox = document.getElementById('sim-result-box');
  if (!slider || !globalData || !globalData.model_stats) return;

  const monthlyCap = parseFloat(slider.value);
  display.textContent = `${formatCurrency(monthlyCap)} / mês`;

  const stats = globalData.model_stats;
  const minInstPichau = 774.51;
  const minInstTerabyte = 813.63;
  const minInstKabum = 929.41;

  let verdictTitle = '';
  let tip = '';
  let statusClass = 'text-green';
  let diff = 0;

  if (monthlyCap >= minInstKabum) {
    verdictTitle = '🎉 Cabe em Qualquer Loja (Pichau, Terabyte e KaBuM!)';
    diff = monthlyCap - minInstPichau;
    tip = `Sua capacidade mensal (${formatCurrency(monthlyCap)}/mês) permite escolher livremente. Na Pichau em 12x (R$ 774,51/mês) ainda sobram <strong>${formatCurrency(diff)}/mês de folga</strong> no seu bolso!`;
    statusClass = 'text-green';
  } else if (monthlyCap >= minInstTerabyte) {
    verdictTitle = '✅ Cabe com Folga na Pichau (12x) e TerabyteShop (12x)';
    diff = monthlyCap - minInstPichau;
    tip = `Você pode adquirir a RTX 5070 Ti na Pichau (12x de R$ 774,51) com <strong>${formatCurrency(diff)}/mês de margem</strong> ou na TerabyteShop (12x de R$ 813,63). Apenas a KaBuM! (10x de R$ 929,41) ficaria apertada.`;
    statusClass = 'text-green';
  } else if (monthlyCap >= minInstPichau) {
    verdictTitle = '🎯 Perfeito para a Pichau em 12x Sem Juros!';
    diff = monthlyCap - minInstPichau;
    tip = `A parcela de 12x de <strong>R$ 774,51 sem juros</strong> na Pichau (Zotac Solid SFF Triplo Fan) cabe com precisão cirúrgica na sua renda mensal de ${formatCurrency(monthlyCap)}/mês!`;
    statusClass = 'text-green';
  } else {
    verdictTitle = '⚠️ Parcela Mínima está em R$ 774,51 / mês (Pichau 12x)';
    diff = minInstPichau - monthlyCap;
    tip = `Faltam apenas <strong>${formatCurrency(diff)}/mês</strong> para atingir a menor parcela sem juros da RTX 5070 Ti (12x de R$ 774,51 na Pichau). Uma pequena economia de R$ ${diff.toFixed(2)} ao mês viabiliza a GPU 4K de 16GB!`;
    statusClass = 'text-accent';
  }

  resultBox.innerHTML = `
    <div class="sim-result-main">
      <h4>Diagnóstico de Capacidade Mensal:</h4>
      <div class="sim-gpu-name" style="font-size:1.15rem; color:#fff;">${verdictTitle}</div>
      <div style="font-size:0.9rem; color:#10b981; font-weight:700; margin-bottom:6px;">
        💳 Menor parcela do mercado: 12x de R$ 774,51 sem juros (Pichau)
      </div>
      <p class="sim-gpu-tip">${tip}</p>
    </div>
    <div class="sim-budget-math">
      <span class="sim-math-label">${monthlyCap >= minInstPichau ? 'Margem Mensal Restante:' : 'Diferença para Parcela 12x:'}</span>
      <div class="sim-math-val ${statusClass}">
        ${formatCurrency(diff)} / mês
      </div>
    </div>
  `;
}

// 9. Tabela Geral de Ofertas com Filtro por Marca, Loja e Parcelamento Sem Juros
function renderOffersTable() {
  if (!globalData || !globalData.offers) return;

  const tbody = document.getElementById('offers-tbody');
  const countLabel = document.getElementById('offers-count-label');
  const filterBrand = document.getElementById('filter-brand')?.value || 'ALL';
  const filterStore = document.getElementById('filter-store')?.value || 'ALL';
  const filterInst = document.getElementById('filter-installments')?.value || 'ALL';
  const filterSort = document.getElementById('filter-sort')?.value || 'installment_asc';

  let offers = globalData.offers.filter(o => o.gpu_model === 'RTX 5070 Ti');

  if (filterBrand !== 'ALL') {
    offers = offers.filter(o => o.brand.toLowerCase() === filterBrand.toLowerCase());
  }

  if (filterStore !== 'ALL') {
    offers = offers.filter(o => o.store_key === filterStore);
  }

  if (filterInst === '12x') {
    offers = offers.filter(o => o.installments_count === 12);
  } else if (filterInst === '10x') {
    offers = offers.filter(o => o.installments_count === 10);
  } else if (filterInst === 'triple_only') {
    offers = offers.filter(o => (o.cooling_type || '').includes('Triplo') || o.title.includes('3X') || o.title.includes('Solid') || o.title.includes('GamingPro'));
  }

  offers.sort((a, b) => {
    if (filterSort === 'installment_asc') return (a.installment_val || 0) - (b.installment_val || 0);
    if (filterSort === 'price_card_asc') return a.price_card - b.price_card;
    if (filterSort === 'score') return b.cost_benefit_score - a.cost_benefit_score;
    if (filterSort === 'fps_cost_4k') return (a.cost_per_fps_4k || 0) - (b.cost_per_fps_4k || 0);
    if (filterSort === 'fps_cost_1440p') return (a.cost_per_fps_1440p || 0) - (b.cost_per_fps_1440p || 0);
    return 0;
  });

  countLabel.textContent = `Exibindo ${offers.length} ofertas consolidadas da RTX 5070 Ti (Parcelamento Sem Juros)`;
  tbody.innerHTML = '';

  offers.forEach(o => {
    const tr = document.createElement('tr');
    
    let storeClass = 'store-kabum';
    if (o.store_key === 'pichau') storeClass = 'store-pichau';
    if (o.store_key === 'terabyte') storeClass = 'store-terabyte';

    const isTripleFan = (o.cooling_type || '').includes('Triplo') || o.title.includes('3X') || o.title.includes('Solid') || o.title.includes('GamingPro');
    const fanTag = isTripleFan ? '<span class="tag-cooling-inline triple">❄️ 3 Fans</span>' : '<span class="tag-cooling-inline dual">🌬️ 2 Fans</span>';
    const promoTag = o.is_limited_promo ? `<span class="tag-promo-inline pulse-glow">${o.promo_badge || '⚡ Promoção'}</span>` : '';

    tr.innerHTML = `
      <td>
        <span class="store-tag ${storeClass}">${o.store_logo || o.store}</span>
      </td>
      <td>
        <strong style="color:#fff;">${o.gpu_model}</strong>
        <div class="gpu-subinfo">${o.vram || '16GB GDDR7'} • ${o.tdp || '300W'}</div>
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
        <span class="price-cash-highlight" style="color:var(--accent-yellow);">${formatCurrency(o.price_card)}</span>
        <div class="gpu-subinfo">Total a prazo</div>
      </td>
      <td class="text-right font-mono">
        <span style="color:#fff; font-weight:600;">${o.installments_count}x sem juros</span>
      </td>
      <td class="text-right">
        <span class="price-15x-highlight" style="color:var(--accent-green); font-weight:700;">${formatCurrency(o.installment_val)}</span>
        <div class="gpu-subinfo">por mês</div>
      </td>
      <td class="text-center font-mono">
        <span style="font-weight:700; color:#c9d1d9;">R$ ${o.cost_per_fps_1440p}</span>
        <div class="gpu-subinfo">145 FPS Médio</div>
      </td>
      <td class="text-center font-mono">
        <span style="font-weight:700; color:#38bdf8;">R$ ${o.cost_per_fps_4k}</span>
        <div class="gpu-subinfo">92 FPS 4K Nativo</div>
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

// 10. Seção Tecnológica DLSS 5 (Novembro/2026)
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
      card.className = `dlss5-card-item highlight-ti-dlss5`;

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

// 11. Parecer Técnico e Veredito Financeiro
function renderVerdict(rec) {
  if (!rec) return;

  const mainTitleEl = document.getElementById('verdict-main-title');
  const mainSummaryEl = document.getElementById('verdict-main-summary');
  if (mainTitleEl) mainTitleEl.textContent = rec.verdict_title || 'Diagnóstico Financeiro de Parcelamento';
  if (mainSummaryEl) mainSummaryEl.innerHTML = rec.verdict_summary ? rec.verdict_summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') : '';

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
        <div class="verdict-price-tag" style="color:#10b981;">${pt.price_ref}</div>
        <div class="verdict-15x-tag" style="color:#eab308;">${pt.price_total_display || pt.price_15x || ''}</div>
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
